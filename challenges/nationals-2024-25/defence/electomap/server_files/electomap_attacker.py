from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from time import sleep
from typing import TYPE_CHECKING, TypedDict
from urllib.parse import urlunsplit

import jwt
from faker import Faker
from httpx import Client as HttpClient
from httpx._models import Response
from paho.mqtt.client import CallbackAPIVersion
from paho.mqtt.client import Client as MqttClient
from siege.attacker.attacker import Attacker  # pyright: ignore
from siege.core.attack_result import AttackResult  # pyright: ignore
from siege.core.log import log, log_error  # pyright: ignore

fake = Faker()

TIMEOUT = 3


def on_mqtt_connect(
    client: MqttClient, userdata: list[str], flags, reason_code, properties
):
    if reason_code.is_failure:
        log_error(f"Connection failure: {reason_code}.")
        raise RuntimeError("Unable to connect to MQTT.")


def on_mqtt_message(client, userdata: list[str], message):
    userdata.append(message.payload.decode())


class ElectomapAttacker(Attacker):
    electomap_host: str
    electomap_port: int
    mqtt_host: str
    mqtt_port_websocket: int
    mqtt_port_tcp: int

    def __init__(self, host: str, port: int):
        super().__init__(host, port)
        self.electomap_host = host
        self.electomap_port = 1337
        self.mqtt_host = self.electomap_host
        self.mqtt_port_websocket = 9001
        self.mqtt_port_tcp = 1883
        self.db_host = self.electomap_host
        self.db_port = 5432

        self.benign_client = BenignClient(
            self.electomap_host,
            self.electomap_port,
            self.mqtt_host,
            self.mqtt_port_websocket,
            self.mqtt_port_tcp,
        )

        self.malicious_client = MaliciousClient(
            self.electomap_host,
            self.electomap_port,
            self.mqtt_host,
            self.mqtt_port_websocket,
            self.mqtt_port_tcp,
        )

    def malicious_request(
        self, id: int, tick: int, sequence_no: int
    ) -> AttackResult:
        try:
            return self.malicious_client.make_request(id, tick, sequence_no)
        except Exception as e:
            log_error(f"Error in malicious request (ID {id}): {e}")
            return AttackResult.RESULT_DOWN

    def benign_request(
        self, id: int, tick: int, sequence_no: int
    ) -> AttackResult:
        try:
            return self.benign_client.make_request(id, tick, sequence_no)
        except Exception as e:
            log_error(f"Error in benign request (ID {id}): {e}")
            return AttackResult.RESULT_DOWN


if TYPE_CHECKING:

    class UserData(TypedDict):
        email: str
        password: str
        name: str
        nationalId: str


class Client:
    def __init__(
        self,
        electomap_host: str,
        electomap_port: int,
        mqtt_host: str,
        mqtt_port_websocket: int,
        mqtt_port_tcp: int,
    ):
        self.electomap_url: str = urlunsplit(
            ("http", f"{electomap_host}:{electomap_port}", "/", None, None)
        )
        self.mqtt_host = mqtt_host
        self.mqtt_port_tcp = mqtt_port_tcp
        self.mqtt_port_websocket = mqtt_port_websocket

    @contextmanager
    def http_client(self):
        try:
            with HttpClient(
                base_url=self.electomap_url, timeout=TIMEOUT
            ) as client:
                yield client
        except Exception as e:
            log_error(e)
            raise

    @contextmanager
    def mqtt_connect(self):
        try:
            mqtt_client = MqttClient(CallbackAPIVersion.VERSION2)
            mqtt_client.on_connect = on_mqtt_connect
            mqtt_client.on_message = on_mqtt_message
            mqtt_client.connect_timeout = TIMEOUT
            mqtt_client.user_data_set([])
            mqtt_client.connect(self.mqtt_host, port=self.mqtt_port_tcp)
            mqtt_client.loop_start()
            yield mqtt_client
            mqtt_client.disconnect()
            mqtt_client.loop_stop()
        except Exception as e:
            log_error(e)
            raise

    @contextmanager
    def mqtt_ws_connect(self):
        try:
            mqtt_ws_client = MqttClient(
                CallbackAPIVersion.VERSION2, transport="websockets"
            )
            mqtt_ws_client.on_connect = on_mqtt_connect
            mqtt_ws_client.on_message = on_mqtt_message
            mqtt_ws_client.connect_timeout = TIMEOUT
            mqtt_ws_client.user_data_set([])
            mqtt_ws_client.connect(
                self.mqtt_host, port=self.mqtt_port_websocket
            )
            mqtt_ws_client.loop_start()
            yield mqtt_ws_client
            mqtt_ws_client.disconnect()
            mqtt_ws_client.loop_stop()
        except Exception as e:
            log_error(e)
            raise

    def create_user(
        self,
        id: int | None = None,
        tick: int | None = None,
        sequence_no: int | None = None,
    ) -> UserData:
        email = uuid.uuid1().hex + fake.email()
        national_id = str(fake.random_number(digits=9, fix_len=True))
        if id is not None and tick is not None and sequence_no is not None:
            national_id = (
                f"{id:02}"
                f"{tick:03}"
                f"{sequence_no:02}"
                f"{fake.random_number(digits=4, fix_len=True)}"
            )

        return {
            "email": email,
            "name": fake.name(),
            "password": fake.password(),
            "nationalId": national_id,
        }

    def register_request(
        self, http_client: HttpClient, user_data: UserData
    ) -> str | None:
        """
        Registers an account, returns the session cookie.
        """
        register_res = http_client.post(
            "/api/auth/register",
            json=user_data,
        )
        if register_res.status_code != 201:
            log(f"Registration failed: {register_res.text}")
            return None

        return register_res.cookies.get("session")

    def login_request(
        self, http_client: HttpClient, email: str, password: str
    ) -> str | None:
        """
        Logs in to an existing account, returns the session cookie
        """
        login_res = http_client.post(
            "/api/auth/signin",
            json={"email": email, "password": password},
        )

        if login_res.status_code != 200:
            log(f"Login failed: {login_res.text}")
            return None

        return login_res.cookies.get("session")

    def vote_request(
        self, http_client: HttpClient, district: str, party: str, vote_key: str
    ) -> Response:
        return http_client.post(
            "/api/votes",
            json={"district": district, "party": party, "voteKey": vote_key},
        )

    def vote_key_request(
        self, http_client: HttpClient, session_token: str
    ) -> str | None:
        vote_key_res = http_client.post(
            "/api/votekeys",
            headers={"Authorization": f"Session {session_token}"},
        )

        if vote_key_res.status_code != 201:
            log_error(
                f"Vote key creation failed ({vote_key_res.status_code}): {vote_key_res.text}"
            )
            return None

        return vote_key_res.json().get("voteKey")

    def party_request(self, http_client: HttpClient) -> Response:
        return http_client.get("/api/parties")

    def district_request(self, http_client: HttpClient) -> Response:
        return http_client.get("/api/districts")


class BenignClient(Client):
    def make_request(
        self, id: int, tick: int, sequence_no: int
    ) -> AttackResult:
        match id:
            case 1:
                return self.cast_vote(tick, sequence_no)
            case 2:
                return self.register_account(tick, sequence_no)
            case 3:
                return self.connect_to_websocket(tick, sequence_no)
            case 4:
                return self.login(tick, sequence_no)
            case 5:
                return self.vote_key(tick, sequence_no)
            case 6:
                return self.get_parties(tick, sequence_no)
            case 7:
                return self.get_districts(tick, sequence_no)
            case 8:
                return self.health(tick, sequence_no)
            case _:
                log(f"Invalid request ID: {id}")
                return AttackResult.RESULT_FAILURE

    def cast_vote(self, tick: int, sequence_no: int) -> AttackResult:
        user_data = self.create_user(id=1, tick=tick, sequence_no=sequence_no)
        with (
            self.http_client() as http_client,
            self.mqtt_ws_connect() as mqtt_ws_client,
        ):
            session_token = self.register_request(http_client, user_data)

            if session_token is None:
                log_error("Session token not set.")
                return AttackResult.RESULT_FAILURE

            vote_key = self.vote_key_request(http_client, session_token)

            if vote_key is None:
                log_error("Vote key not set.")
                return AttackResult.RESULT_FAILURE

            party_res = self.party_request(http_client)
            district_res = self.district_request(http_client)

            if party_res.status_code != 200 or district_res.status_code != 200:
                log_error("Error retrieving parties or districts.")
                return AttackResult.RESULT_FAILURE

            parties = party_res.json()
            districts = district_res.json()

            selected_party = parties[sequence_no % len(parties)]
            selected_district = districts[sequence_no % len(districts)]

            party_id = selected_party.get("id", "")
            district_id = selected_district.get("id", "")

            mqtt_ws_client.subscribe("vote-counts")
            vote_res = self.vote_request(
                http_client, district_id, party_id, vote_key
            )

            if vote_res.status_code != 204:
                log_error(
                    f"Vote response unsuccessful ({vote_res.status_code}): {vote_res.text}"
                )
                return AttackResult.RESULT_FAILURE

            # Make sure we get all the possible MQTT data
            sleep(1)

            if len(mqtt_ws_client.user_data_get()) < 1:
                log_error("No messages obtained.")
                return AttackResult.RESULT_FAILURE

            messages: list[str] = mqtt_ws_client.user_data_get()
            for message in messages:
                message_data = json.loads(message)

                voted_party_id = message_data.get("partyId")
                voted_district_id = message_data.get("districtId")

                if voted_party_id != party_id:
                    continue

                if voted_district_id != district_id:
                    continue

                return AttackResult.RESULT_SUCCESS

            return AttackResult.RESULT_FAILURE

    def register_account(self, tick: int, sequence_no: int) -> AttackResult:
        user_data = self.create_user(id=2, tick=tick, sequence_no=sequence_no)
        with self.http_client() as http_client:
            session_token = self.register_request(http_client, user_data)

            if session_token is None:
                return AttackResult.RESULT_FAILURE

            return AttackResult.RESULT_SUCCESS

    def connect_to_websocket(self, tick: int, sequence_no: int) -> AttackResult:
        with self.mqtt_ws_connect() as mqtt_ws_client:
            mqtt_ws_client.subscribe("vote-counts")

            return AttackResult.RESULT_SUCCESS

    def login(self, tick: int, sequence_no: int) -> AttackResult:
        user_data = self.create_user(id=4, tick=tick, sequence_no=sequence_no)
        with self.http_client() as http_client:
            session_token = self.register_request(http_client, user_data)

            if session_token is None:
                return AttackResult.RESULT_FAILURE

            session_token = self.login_request(
                http_client, user_data["email"], user_data["password"]
            )

            if session_token is None:
                return AttackResult.RESULT_FAILURE
            return AttackResult.RESULT_SUCCESS

    def vote_key(self, tick: int, sequence_no: int) -> AttackResult:
        user_data = self.create_user(id=5, tick=tick, sequence_no=sequence_no)
        with self.http_client() as http_client:
            session_token = self.register_request(http_client, user_data)

            if session_token is None:
                return AttackResult.RESULT_FAILURE

            vote_key = self.vote_key_request(http_client, session_token)

            if vote_key is None:
                return AttackResult.RESULT_FAILURE
            return AttackResult.RESULT_SUCCESS

    def get_parties(self, tick: int, sequence_no: int) -> AttackResult:
        with self.http_client() as http_client:
            party_response = self.party_request(http_client)
            if party_response.status_code != 200:
                return AttackResult.RESULT_FAILURE
            return AttackResult.RESULT_SUCCESS

    def get_districts(self, tick: int, sequence_no: int) -> AttackResult:
        with self.http_client() as http_client:
            party_response = self.district_request(http_client)
            if party_response.status_code != 200:
                return AttackResult.RESULT_FAILURE
            return AttackResult.RESULT_SUCCESS

    def health(self, tick: int, sequence_no: int) -> AttackResult:
        with self.http_client() as http_client:
            health_res = http_client.get("/")
            if health_res.status_code != 200:
                return AttackResult.RESULT_FAILURE
            return AttackResult.RESULT_SUCCESS


class MaliciousClient(Client):
    def make_request(
        self, id: int, tick: int, sequence_no: int
    ) -> AttackResult:
        match id:
            case 1:
                return self.mqtt_intercept_vote(tick, sequence_no)
            case 2:
                return self.double_vote(tick, sequence_no)
            case 3:
                return self.forged_vote_key(tick, sequence_no)
            case 4:
                return self.unverified_vote_key(tick, sequence_no)
            case 5:
                return self.duplicate_national_id(tick, sequence_no)
            case 6:
                return self.websocket_fake_vote(tick, sequence_no)
            case 7:
                return self.exposed_national_id(tick, sequence_no)
            case 8:
                return self.test_account(tick, sequence_no)
            case _:
                log(f"Invalid request ID: {id}")
                return AttackResult.RESULT_FAILURE

    def mqtt_intercept_vote(self, tick: int, sequence_no: int) -> AttackResult:
        # Send a vote, then intercept it via the MQTT
        user_data = self.create_user(id=11, tick=tick, sequence_no=sequence_no)
        with (
            self.http_client() as http_client,
        ):
            session_token = self.register_request(http_client, user_data)

            if session_token is None:
                return AttackResult.RESULT_FAILURE

            vote_key = self.vote_key_request(http_client, session_token)

            if vote_key is None:
                return AttackResult.RESULT_FAILURE

            party_res = self.party_request(http_client)
            district_res = self.district_request(http_client)

            if party_res.status_code != 200 or district_res.status_code != 200:
                return AttackResult.RESULT_FAILURE

            parties = party_res.json()
            districts = district_res.json()

            selected_party = parties[sequence_no % len(parties)]
            selected_district = districts[sequence_no % len(districts)]

            party_id = selected_party.get("id", "")
            district_id = selected_district.get("id", "")

            try:
                with self.mqtt_connect() as mqtt_client:
                    mqtt_client.subscribe("votes")

                    vote_res = self.vote_request(
                        http_client, district_id, party_id, vote_key
                    )

                    if vote_res.status_code != 204:
                        log_error(
                            f"Failed to send vote ({vote_res.status_code}): {vote_res.text}"
                        )
                        return AttackResult.RESULT_FAILURE

                    sleep(1)

                    if len(mqtt_client.user_data_get()) < 1:
                        log_error("No user data present.")
                        return AttackResult.RESULT_FAILURE

                    messages: list[str] = mqtt_client.user_data_get()
                    for message in messages:
                        message_data = json.loads(message)

                        # Here there is no "Id" in the payload
                        voted_party_id = message_data.get("party")
                        voted_district_id = message_data.get("district")

                        if voted_party_id != party_id:
                            continue

                        if voted_district_id != district_id:
                            continue

                        return AttackResult.RESULT_SUCCESS
                    return AttackResult.RESULT_FAILURE
            except RuntimeError:
                log(
                    "Failed to connect to MQTT server. Treating this as an attack failure."
                )
                return AttackResult.RESULT_FAILURE
            except Exception as e:
                log_error(e)
                raise

    def double_vote(self, tick: int, sequence_no: int) -> AttackResult:
        user_data = self.create_user(id=12, tick=tick, sequence_no=sequence_no)
        with (
            self.http_client() as http_client,
            self.mqtt_ws_connect() as mqtt_ws_client,
        ):
            session_token = self.register_request(http_client, user_data)

            if session_token is None:
                return AttackResult.RESULT_FAILURE

            vote_key = self.vote_key_request(http_client, session_token)

            if vote_key is None:
                return AttackResult.RESULT_FAILURE

            # Maybe I should offload this all to a separate function

            party_res = self.party_request(http_client)
            district_res = self.district_request(http_client)

            if party_res.status_code != 200 or district_res.status_code != 200:
                return AttackResult.RESULT_FAILURE

            parties = party_res.json()
            districts = district_res.json()

            selected_party = parties[sequence_no % len(parties)]
            selected_district = districts[sequence_no % len(districts)]

            party_id = selected_party.get("id", "")
            district_id = selected_district.get("id", "")

            votes_confirmed = 0
            mqtt_ws_client.subscribe("vote-counts")

            for _ in range(2):
                vote_res = self.vote_request(
                    http_client, district_id, party_id, vote_key
                )
                if vote_res.status_code != 204:
                    return AttackResult.RESULT_FAILURE

            # Make sure all the MQTT stuff comes in
            sleep(1)

            if len(mqtt_ws_client.user_data_get()) < 1:
                return AttackResult.RESULT_FAILURE

            messages: list[str] = mqtt_ws_client.user_data_get()
            for message in messages:
                message_data = json.loads(message)
                voted_party_id = message_data.get("partyId")
                voted_district_id = message_data.get("districtId")

                if voted_party_id != party_id:
                    continue

                if voted_district_id != district_id:
                    continue

                votes_confirmed += 1

            if votes_confirmed < 2:
                return AttackResult.RESULT_FAILURE

            return AttackResult.RESULT_SUCCESS

    def forged_vote_key(self, tick: int, sequence_no: int) -> AttackResult:
        user_data = self.create_user(id=13, tick=tick, sequence_no=sequence_no)
        with self.http_client() as http_client:
            session_token = self.register_request(http_client, user_data)

            if session_token is None:
                return AttackResult.RESULT_FAILURE

            vote_key = self.vote_key_request(http_client, session_token)

            if vote_key is None:
                return AttackResult.RESULT_FAILURE

            payload = jwt.decode(vote_key, options={"verify_signature": False})

            vote_key = jwt.encode(
                payload, algorithm="HS256", key="default-jwt-secret"
            )

            party_res = self.party_request(http_client)
            district_res = self.district_request(http_client)

            if party_res.status_code != 200 or district_res.status_code != 200:
                return AttackResult.RESULT_FAILURE

            parties = party_res.json()
            districts = district_res.json()

            selected_party = parties[sequence_no % len(parties)]
            selected_district = districts[sequence_no % len(districts)]

            party_id = selected_party.get("id", "")
            district_id = selected_district.get("id", "")

            vote_res = self.vote_request(
                http_client, district_id, party_id, vote_key
            )

            if vote_res.status_code != 204:
                return AttackResult.RESULT_FAILURE

            return AttackResult.RESULT_SUCCESS

    def unverified_vote_key(self, tick: int, sequence_no: int) -> AttackResult:
        user_data = self.create_user(id=14, tick=tick, sequence_no=sequence_no)
        with self.http_client() as http_client:
            session_token = self.register_request(http_client, user_data)

            if session_token is None:
                return AttackResult.RESULT_FAILURE

            vote_key = self.vote_key_request(http_client, session_token)

            if vote_key is None:
                return AttackResult.RESULT_FAILURE

            payload = jwt.decode(vote_key, options={"verify_signature": False})

            vote_key = jwt.encode(payload, algorithm="HS256", key="")

            party_res = self.party_request(http_client)
            district_res = self.district_request(http_client)

            if party_res.status_code != 200 or district_res.status_code != 200:
                return AttackResult.RESULT_FAILURE

            parties = party_res.json()
            districts = district_res.json()

            selected_party = parties[sequence_no % len(parties)]
            selected_district = districts[sequence_no % len(districts)]

            party_id = selected_party.get("id", "")
            district_id = selected_district.get("id", "")

            vote_res = self.vote_request(
                http_client, district_id, party_id, vote_key
            )

            if vote_res.status_code != 204:
                return AttackResult.RESULT_FAILURE

            return AttackResult.RESULT_SUCCESS

    def duplicate_national_id(
        self, tick: int, sequence_no: int
    ) -> AttackResult:
        user_data = self.create_user(id=15, tick=tick, sequence_no=sequence_no)
        user_data_2 = self.create_user()
        user_data_2["nationalId"] = user_data["nationalId"]

        with self.http_client() as http_client:
            session_token = self.register_request(http_client, user_data)

            if session_token is None:
                return AttackResult.RESULT_FAILURE

            session_token_2 = self.register_request(http_client, user_data_2)

            if session_token_2 is None:
                return AttackResult.RESULT_FAILURE

            return AttackResult.RESULT_SUCCESS

    def websocket_fake_vote(self, tick: int, sequence_no: int) -> AttackResult:
        with (
            self.http_client() as http_client,
            self.mqtt_ws_connect() as mqtt_ws_client,
        ):
            mqtt_ws_client.subscribe("vote-counts")
            party_res = self.party_request(http_client)
            district_res = self.district_request(http_client)

            if party_res.status_code != 200 or district_res.status_code != 200:
                return AttackResult.RESULT_FAILURE

            parties = party_res.json()
            districts = district_res.json()

            selected_party = parties[sequence_no % len(parties)]
            selected_district = districts[sequence_no % len(districts)]

            party_id = selected_party.get("id", "")
            district_id = selected_district.get("id", "")

            mqtt_ws_client.publish(
                "vote-counts",
                payload=json.dumps(
                    {"partyId": party_id, "districtId": district_id}
                ),
            )

            sleep(1)

            if len(mqtt_ws_client.user_data_get()) < 1:
                return AttackResult.RESULT_FAILURE

            messages: list[str] = mqtt_ws_client.user_data_get()
            for message in messages:
                message_data = json.loads(message)

                voted_party_id = message_data.get("partyId")
                voted_district_id = message_data.get("districtId")

                if voted_party_id != party_id:
                    continue

                if voted_district_id != district_id:
                    continue

                return AttackResult.RESULT_SUCCESS

            return AttackResult.RESULT_FAILURE

    def exposed_national_id(self, tick: int, sequence_no: int) -> AttackResult:
        user_data = self.create_user(id=17, tick=tick, sequence_no=sequence_no)
        with (
            self.http_client() as http_client,
        ):
            session_token = self.register_request(http_client, user_data)
            if session_token is None:
                return AttackResult.RESULT_FAILURE

            vote_key = self.vote_key_request(http_client, session_token)
            if vote_key is None:
                # Should this be down instead of failed?
                return AttackResult.RESULT_FAILURE

            payload = jwt.decode(vote_key, options={"verify_signature": False})

            national_id = payload.get("sub", None)

            if national_id != user_data["nationalId"]:
                return AttackResult.RESULT_FAILURE

            return AttackResult.RESULT_SUCCESS

    def test_account(self, tick: int, sequence_no: int) -> AttackResult:
        with self.http_client() as http_client:
            session_token = self.login_request(
                http_client, "test@test.com", "Password1!"
            )
            if session_token is None:
                return AttackResult.RESULT_FAILURE
            return AttackResult.RESULT_SUCCESS
