import asyncio
import json
import time
from typing import Any

import httpx
import structlog
from paho.mqtt.client import Client as MqttClient
from paho.mqtt.enums import CallbackAPIVersion

logger = structlog.stdlib.get_logger()


async def get_session_token(client: httpx.AsyncClient) -> str | None:
    signin_res = await client.post(
        "/api/auth/signin",
        json={"email": "test@test.com", "password": "Password1!"},
    )
    if signin_res.status_code != 200:
        await logger.aerror(signin_res.text)
        return None

    sessionToken = signin_res.cookies.get("session")
    await logger.adebug(
        "Signed in.",
        response=signin_res,
        session_cookie=sessionToken,
    )
    return sessionToken


async def make_vote_package(
    districts: list[dict[str, Any]],
    parties: list[dict[str, Any]],
    vote_key: str | None,
) -> dict[str, str]:
    chosen_district = districts[0]
    chosen_party = parties[0]
    package = {
        "district": chosen_district.get("id", ""),
        "party": chosen_party.get("id", ""),
        "voteKey": vote_key,
    }
    await logger.adebug("Vote package made.", package=package)
    return package


async def send_vote(client: httpx.AsyncClient, package: dict[str, str]):
    vote_res = await client.post("/api/votes", json=package)
    await logger.adebug("Voted.", response=vote_res)


def on_mqtt_message(client, userdata: list, message):
    userdata.append(message.payload.decode())


async def main():
    async with (
        httpx.AsyncClient(base_url="http://localhost:1337") as electomap_client,
    ):
        sessionToken = await get_session_token(electomap_client)
        districts_api_call = asyncio.create_task(
            electomap_client.get("/api/districts")
        )
        parties_api_call = asyncio.create_task(
            electomap_client.get("/api/parties")
        )
        vote_key_api_call = asyncio.create_task(
            electomap_client.post(
                "/api/votekeys",
                headers={"Authorization": f"Session {sessionToken}"},
            )
        )
        [districts_res, parties_res, vote_key_res] = await asyncio.gather(
            districts_api_call, parties_api_call, vote_key_api_call
        )
        if districts_res.status_code != 200:
            await logger.aerror(districts_res.text)
            return

        if parties_res.status_code != 200:
            await logger.aerror(parties_res.text)
            return

        if vote_key_res.status_code != 201:
            await logger.aerror(
                "Vote key not created: %s",
                vote_key_res.text,
                json=vote_key_res.cookies,
            )
            return

        districts = districts_res.json()
        parties = parties_res.json()
        vote_key = vote_key_res.json().get("voteKey")

        vote_package = await make_vote_package(districts, parties, vote_key)
        mqtt_client = MqttClient(
            CallbackAPIVersion.VERSION2, transport="websockets"
        )
        mqtt_client.on_message = on_mqtt_message
        mqtt_client.connect("localhost", port=9001)
        mqtt_client.loop_start()
        mqtt_client.user_data_set([])
        mqtt_client.subscribe("vote-counts")
        await send_vote(electomap_client, vote_package)

        while len(mqtt_client.user_data_get()) <= 0:
            time.sleep(0.01)

        await logger.adebug("Got message.", data=mqtt_client.user_data_get())

        messages: list[str] = mqtt_client.user_data_get()

        for message in messages:
            message_data = json.loads(message)

            voted_party_id = message_data.get("partyId")
            voted_district_id = message_data.get("districtId")

            if voted_party_id != parties[0].get("id", ""):
                continue

            if voted_district_id != districts[0].get("id", ""):
                continue

            await logger.adebug(
                "Votes are a match!",
                voted_district_id=voted_district_id,
                voted_party_id=voted_party_id,
            )

        mqtt_client.disconnect()
        mqtt_client.loop_stop()


asyncio.run(main())
