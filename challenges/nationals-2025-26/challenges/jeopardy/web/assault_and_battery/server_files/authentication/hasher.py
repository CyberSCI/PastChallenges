import base64
import os
from hashlib import md5
from typing import override

import argon2
import structlog
from django.contrib.auth.hashers import Argon2PasswordHasher

logger = structlog.stdlib.get_logger("reclaimer_central.authentication")

DEFAULT_PEPPER = "jason-is-a-dingus"

PROFILE = argon2.profiles.RFC_9106_LOW_MEMORY
ITERATIONS: int = 1000
PEPPER: str = os.environ.get("PASSWORD_PEPPER", DEFAULT_PEPPER)

assert PEPPER != DEFAULT_PEPPER


class ReclaimerPasswordHasher(Argon2PasswordHasher):
    time_cost: int = PROFILE.time_cost
    memory_cost: int = PROFILE.memory_cost
    parallelism: int = PROFILE.parallelism
    hash_len: int = PROFILE.hash_len
    salt_len: int = PROFILE.salt_len

    algorithm: str = "argon2"

    def reinforce_hash(self, data_in: str, reinforcer: str) -> str:
        hash_input: str = f"{data_in}{reinforcer}"
        # Don't want this to be too slow,
        # we're still working with limited compute here
        result = md5(hash_input.encode()).hexdigest()
        return result

    def reinforce(self, password: str, salt: str) -> str:
        data = self.reinforce_hash(password, salt)
        data = self.reinforce_hash(password, PEPPER)

        for index in range(ITERATIONS):
            logger.debug("Reinforcing hash...", index=index, data=data)
            data = self.reinforce_hash(data, PEPPER[index % len(PEPPER)])

        return data

    def get_hasher(self):
        return argon2.PasswordHasher(
            time_cost=self.time_cost,
            memory_cost=self.memory_cost,
            parallelism=self.parallelism,
            hash_len=self.hash_len,
            type=argon2.Type.ID,
        )

    def decode(self, encoded: str):
        algorithm, rest = encoded.split("$", 1)
        assert algorithm == self.algorithm
        params = argon2.extract_parameters("$" + rest)
        variety, *_, b64salt, hash = rest.split("$")
        # Add padding.
        b64salt += "=" * (-len(b64salt) % 4)
        salt = base64.b64decode(b64salt).decode("latin1")
        return {
            "algorithm": algorithm,
            "hash": hash,
            "memory_cost": params.memory_cost,
            "parallelism": params.parallelism,
            "salt": salt,
            "time_cost": params.time_cost,
            "variety": variety,
            "version": params.version,
            "params": params,
        }

    @override
    def encode(self, password: str, salt: str):
        # _ = structlog.contextvars.bind_contextvars(salt=salt)
        data = self.reinforce(password, salt)

        hasher = self.get_hasher()

        hashed = hasher.hash(data, salt=salt.encode())
        logger.debug("Hashing complete.", hash=hashed)

        return self.algorithm + hashed

    @override
    def verify(self, password: str, encoded: str):
        decoded_data = self.decode(encoded)
        salt = str(decoded_data.get("salt", ""))
        # _ = structlog.contextvars.bind_contextvars(salt=salt)

        _, rest = encoded.split("$", 1)

        hashed_pw = f"${rest}"

        data = self.reinforce(password, salt)
        hasher = self.get_hasher()

        try:
            logger.debug("Comparing...", hash=hashed_pw, data=data)
            return hasher.verify(hashed_pw, data)
        except argon2.exceptions.VerificationError as e:
            logger.error(str(e))
            return False
