import asyncio

from faker import Faker
from httpx import AsyncClient


async def sanity_check():
    gen = Faker()
    async with AsyncClient(base_url="http://localhost:8000") as http_client:
        email = gen.email()
        password = gen.password()
        first_name = gen.first_name()
        last_name = gen.last_name()
        national_id = gen.random_number(digits=9, fix_len=True)
        date_of_birth = gen.date_of_birth()
        await http_client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "first_name": first_name,
                "last_name": last_name,
                "national_id": national_id,
                "date_of_birth": date_of_birth,
            },
        )


def main():
    asyncio.run(sanity_check())


if __name__ == "__main__":
    main()
