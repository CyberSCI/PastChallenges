import asyncio
import json
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import override

from httpx import AsyncClient

SERVER_FILES = Path(__file__).parent.parent.absolute()
SCRIPT_DATA = SERVER_FILES / "scripts" / "data"


@dataclass
class Credentials:
    username: str
    password: str

    @classmethod
    def from_dict(cls, data: dict[str, str]):
        return cls(username=data["username"], password=data["password"])

    @override
    def __hash__(self) -> int:
        return hash(f"{self.username}:{self.password}")

    def to_dict(self) -> dict[str, str]:
        return {"username": self.username, "password": self.password}


with open(SCRIPT_DATA / "creds.json") as creds_fd:
    ALL_CREDENTIALS: set[Credentials] = set(
        [Credentials.from_dict(data) for data in json.load(creds_fd)]
    )

POST_COMMENTS = [
    "Noted.",
    "Thanks.",
    "Got it.",
    "Acknowledged.",
    "Will do.",
    "Roger.",
    "Copy that.",
    "Understood.",
]


class UserBot:
    bot_id: int
    hostname: str
    app_port: int = 8000

    credentials: Credentials

    @property
    def base_url(self):
        return f"http://{self.hostname}:{self.app_port}"

    def __init__(
        self, hostname: str, bot_id: int, credentials: Credentials | None = None
    ):
        self.bot_id = bot_id
        self.hostname = hostname
        if credentials is not None:
            self.credentials = credentials
            return
        self.credentials = random.choice(list(ALL_CREDENTIALS))
        ALL_CREDENTIALS.remove(self.credentials)
        self._debug(f"Current bot user: {self.credentials.username}")

    def _debug(self, message: str):
        print(f"Bot {self.bot_id}: {message}")

    async def login(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/login/", json=self.credentials.to_dict()
        )
        if response.status_code != 200:
            return False
        token = response.json().get("token")
        client.headers["Authorization"] = f"Token {token}"
        return True

    async def list_bulletins(self, client: AsyncClient):
        _ = await client.get("/api/bulletins/")

    async def view_random_bulletin(self, client: AsyncClient):
        bulletin_res = await client.get("/api/bulletins/")
        if bulletin_res.status_code != 200:
            self._debug("Could not get bulletin")
            return
        bulletin_id = random.randint(1, 4)
        _ = await client.get(f"/api/bulletins/{bulletin_id}/")

    async def list_posts(self, client: AsyncClient):
        _ = await client.get("/api/bulletins/posts/")

    async def view_random_post(self, client: AsyncClient):
        response = await client.get("/api/bulletins/posts/")
        if response.status_code != 200:
            self._debug("Could not get posts")
            return
        posts = response.json()
        if posts:
            post = random.choice(posts)
            _ = await client.get(f"/api/bulletins/posts/{post['id']}/")

    async def comment_on_post(self, client: AsyncClient):
        response = await client.get("/api/bulletins/posts/")
        if response.status_code != 200:
            self._debug(
                f"Could not get comments (status code {response.status_code})"
            )
            return
        posts = response.json()
        if posts:
            post = random.choice(posts)
            _ = await client.post(
                f"/api/bulletins/posts/{post['id']}/comments/",
                json={
                    "body": random.choice(POST_COMMENTS),
                },
            )

    async def list_comments(self, client: AsyncClient):
        _ = await client.get("/api/bulletins/comments/")

    async def view_logs(self, client: AsyncClient):
        levels = ["info", "warning", "error", "debug"]
        _ = await client.get(
            "/api/system/logs/",
            params={"level": random.choice(levels), "size": 10},
        )

    async def run(self):
        actions = [
            self.list_bulletins,
            self.view_random_bulletin,
            self.list_posts,
            self.view_random_post,
            self.comment_on_post,
            self.list_comments,
            self.view_logs,
        ]
        async with AsyncClient(base_url=self.base_url) as client:
            await asyncio.sleep(random.randint(1, 4))
            logged_in = await self.login(client)
            if not logged_in:
                self._debug("Could not log in.")
                return
            selected = random.sample(actions, k=random.randint(3, 6))
            for action in selected:
                await asyncio.sleep(random.uniform(0.5, 2.0))
                try:
                    await action(client)
                except Exception as e:
                    self._debug(f"{action.__name__} failed: {e}")


class AdminBot(UserBot):
    def __init__(self, hostname: str, bot_id: int):
        return super().__init__(
            hostname,
            bot_id,
            credentials=Credentials(
                username="O-1",
                password=os.environ.get("ADMIN_PASSWORD", "oops"),
            ),
        )


async def main():
    hostname = os.environ.get("APP_HOST", "localhost")
    bots = [UserBot(hostname, i) for i in range(5)] + [AdminBot(hostname, 5)]
    bot_tasks: list[asyncio.Task[None]] = []
    async with asyncio.TaskGroup() as tg:
        for bot in bots:
            task = tg.create_task(bot.run())
            bot_tasks.append(task)


if __name__ == "__main__":
    asyncio.run(main())
