#!/usr/bin/env python

import string
from base64 import b64encode
from pathlib import Path

from cryptography.hazmat.backends import (
    default_backend as crypto_default_backend,
)
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa

USERS: list[str] = ["admin", "sofia.bernhard", "michael.fateh"]

B64_STANDARD = string.ascii_uppercase + string.ascii_lowercase + string.digits + "+/"
B64_CUSTOM = "".join(reversed(B64_STANDARD))

KEY_PATH = Path("keys")


def custom_encode(data: bytes):
    partly_encoded_data = b64encode(data).decode()
    full_encoded_data = bytes(
        partly_encoded_data.translate(
            partly_encoded_data.maketrans(B64_STANDARD, B64_CUSTOM)
        ),
        "utf-8",
    )
    return full_encoded_data


def create_key(user: str):
    key = rsa.generate_private_key(
        backend=crypto_default_backend, public_exponent=65537, key_size=2048
    )

    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.OpenSSH,
        crypto_serialization.NoEncryption(),
    )

    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH,
    )

    encoded_public_key = custom_encode(public_key)

    with (
        open(KEY_PATH / user, "wb+") as private_key_fd,
        open(KEY_PATH / f"{user}.pub", "wb+") as public_key_fd,
        open(KEY_PATH / f"{user}.pub.encoded", "wb+") as encoded_public_key_fd,
    ):
        private_key_fd.write(private_key)
        public_key_fd.write(public_key)
        encoded_public_key_fd.write(encoded_public_key)


def main():
    for user in USERS:
        create_key(user)


main()
