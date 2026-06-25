import base64
import os
from typing import override

from django.contrib.auth.models import User
from django.db import models

from crypto.vault import (
    create_key_pair,
    decrypt_content,
    decrypt_encoded_content,
    derive_key,
    encrypt_content,
)
from shared.types import ByteField


class EncryptionKey(models.Model):
    wrapped_key: ByteField = models.BinaryField()
    key_nonce: ByteField = models.BinaryField()

    class Meta:
        abstract: bool = True

    @override
    def __str__(self) -> str:
        return super().__str__()

    @classmethod
    def create_key(cls, wrapper_key: bytes):
        key = os.urandom(32)
        wrapped_key, nonce = encrypt_content(key, wrapper_key)
        return wrapped_key, nonce

    def encrypt(self, plaintext: str, wrapper_key: bytes) -> tuple[str, bytes]:
        key = self._retrieve_key(wrapper_key)
        ciphertext, nonce = encrypt_content(plaintext.encode(), key)
        encoded_ciphertext = base64.b64encode(ciphertext).decode()
        return encoded_ciphertext, nonce

    def decrypt(
        self, encoded_ciphertext: str, nonce: bytes, wrapper_key: bytes
    ) -> bytes:
        key = self._retrieve_key(wrapper_key)
        plaintext = decrypt_encoded_content(encoded_ciphertext, key, nonce)
        return plaintext

    def _retrieve_key(self, wrapper_key: bytes):
        decrypted_key = decrypt_content(
            self.wrapped_key, wrapper_key, self.key_nonce
        )
        return decrypted_key


class UserEncryptionKey(EncryptionKey):
    """Stores user's encryption key set"""

    user: models.OneToOneField[User] = models.OneToOneField(
        User, on_delete=models.CASCADE
    )
    key_salt: models.BinaryField[bytes, bytes] = models.BinaryField()

    # Asymmetric keypair for receiving shared content

    public_key: ByteField = (
        models.BinaryField()
    )  # X25519 or RSA public key (stored plaintext)
    wrapped_private_key: ByteField = (
        models.BinaryField()
    )  # Private key wrapped by master_key
    private_key_nonce: ByteField = models.BinaryField()

    @override
    def __str__(self) -> str:
        return super().__str__()

    def get_password_key(self, password: str) -> bytes:
        master_key = derive_key(password, self.key_salt)
        return master_key

    def get_user_key(self, password: str) -> bytes:
        password_key = self.get_password_key(password)
        return self._retrieve_key(password_key)

    @classmethod
    def setup(cls, user: User, password: str):
        master_key = os.urandom(32)
        salt = os.urandom(16)
        password_key = derive_key(password, salt)
        wrapped_master, nonce = encrypt_content(master_key, password_key)
        public_key, wrapped_private_key, private_key_nonce = create_key_pair(
            master_key
        )

        key = cls.objects.create(
            user=user,
            wrapped_key=wrapped_master,
            key_salt=salt,
            key_nonce=nonce,
            public_key=public_key,
            wrapped_private_key=wrapped_private_key,
            private_key_nonce=private_key_nonce,
        )
        key.save()

    def retrieve_private_key(self, wrapper_key: bytes):
        decrypted_private_key = decrypt_content(
            self.wrapped_private_key, wrapper_key, self.private_key_nonce
        )
        return decrypted_private_key
