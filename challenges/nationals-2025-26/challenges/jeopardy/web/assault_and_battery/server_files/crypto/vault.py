import base64
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# https://cryptography.io/en/latest/hazmat/primitives/asymmetric/x25519/


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256-bit key for AES-256
        salt=salt,
        iterations=600_000,  # OWASP recommended minimum
    )
    return kdf.derive(password.encode())


def create_key_pair(master_key: bytes) -> tuple[bytes, bytes, bytes]:
    private_key = X25519PrivateKey.generate()
    public_key = private_key.public_key()

    wrapped_private_key, private_key_nonce = encrypt_content(
        private_key.private_bytes_raw(), master_key
    )

    return (
        public_key.public_bytes_raw(),
        wrapped_private_key,
        private_key_nonce,
    )


def encrypt_content(plaintext: bytes, key: bytes) -> tuple[bytes, bytes]:
    """Returns (ciphertext, nonce)"""
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return ciphertext, nonce


def decrypt_content(ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
    aesgcm = AESGCM(key)
    try:
        result = aesgcm.decrypt(nonce, ciphertext, None)
        return result
    except InvalidTag as e:
        raise ValueError(
            "Unable to decrypt content. "
            + "Please ensure you are using the correct key."
        ) from e


def decrypt_encoded_content(
    encoded_ciphertext: str, key: bytes, nonce: bytes
) -> bytes:
    ciphertext = base64.b64decode(encoded_ciphertext)
    return decrypt_content(ciphertext, key, nonce)


def wrap_shared_key(
    post_key: bytes,
    sender_private_key_bytes: bytes,
    recipient_public_key_bytes: bytes,
) -> tuple[bytes, bytes]:
    sender_private = X25519PrivateKey.from_private_bytes(
        sender_private_key_bytes
    )
    recipient_public = X25519PublicKey.from_public_bytes(
        recipient_public_key_bytes
    )
    shared_secret = sender_private.exchange(recipient_public)
    wrapped_key, nonce = encrypt_content(post_key, shared_secret)
    return wrapped_key, nonce


def unwrap_shared_key(
    wrapped_key: bytes,
    nonce: bytes,
    sender_public_key_bytes: bytes,
    recipient_private_key_bytes: bytes,
) -> bytes:
    """
    Recovers a shared key using recipient's private key and the sender's public key.
    """

    recipient_private = X25519PrivateKey.from_private_bytes(
        recipient_private_key_bytes
    )
    ephemeral_public = X25519PublicKey.from_public_bytes(
        sender_public_key_bytes
    )
    shared_secret = recipient_private.exchange(ephemeral_public)
    return decrypt_content(wrapped_key, shared_secret, nonce)
