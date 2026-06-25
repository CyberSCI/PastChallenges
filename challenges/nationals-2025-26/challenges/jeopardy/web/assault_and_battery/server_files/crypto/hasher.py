import os
from hashlib import sha256
from typing import override

import argon2
import structlog
from django.contrib.auth.hashers import (
    BCryptSHA256PasswordHasher,
)

logger = structlog.stdlib.get_logger("reclaimer_central.authentication")

DEFAULT_PEPPER = "jason-is-a-dingus"

# CRITICAL: CHEAPEST IS FINE, WE LITERALLY CAN'T USE ARGON2 OTHERWISE
PROFILE = argon2.profiles.CHEAPEST
ITERATIONS: int = 1000
PEPPER: str = os.environ.get("PASSWORD_PEPPER", DEFAULT_PEPPER)

assert PEPPER != DEFAULT_PEPPER


class ReclaimerPasswordHasher(BCryptSHA256PasswordHasher):
    def reinforce_hash(self, data_in: str, reinforcer: str) -> str:
        hash_input: str = f"{data_in}{reinforcer}"
        result = sha256(hash_input.encode()).hexdigest()
        return result

    def reinforce(self, password: str, salt: str) -> str:
        data = self.reinforce_hash(password, salt)
        data = self.reinforce_hash(password, PEPPER)

        for index in range(ITERATIONS):
            logger.debug("Reinforcing hash...", index=index, data=data)
            data = self.reinforce_hash(data, PEPPER)

        return data

    def decode(self, encoded: str) -> dict[str, str | int]:
        algorithm, empty, algostr, work_factor, data = encoded.split("$", 4)
        assert algorithm == self.algorithm
        return {
            "algorithm": algorithm,
            "algostr": algostr,
            "checksum": data[22:],
            "salt": data[:22],
            "work_factor": int(work_factor),
        }

    @override
    def encode(self, password: str, salt: str) -> str:
        reinforced_password = self.reinforce(password, salt)
        return super().encode(reinforced_password, salt)

    @override
    def verify(self, password: str, encoded: str) -> bool:
        decoded = self.decode(encoded)
        reinforced_password = self.reinforce(password, str(decoded["salt"]))
        return super().verify(reinforced_password, encoded)
