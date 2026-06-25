import base64
from collections.abc import Iterable
from datetime import datetime
from typing import override

import structlog
from django.contrib.auth.models import User
from django.db import models

from authentication.models import (
    EncryptionKey,
    UserEncryptionKey,
)
from crypto.vault import (
    decrypt_encoded_content,
    encrypt_content,
    unwrap_shared_key,
    wrap_shared_key,
)
from shared.types import OptionalByteField

logger = structlog.stdlib.get_logger("reclaimer_central.bulletin")


def title_field(max_length: int = 250) -> models.TextField[str, str]:
    return models.TextField(max_length=max_length)


def body_field(max_length: int = 3000) -> models.TextField[str, str]:
    return models.TextField(max_length=max_length)


class CommonObject(models.Model):
    created_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )
    updated_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        abstract: bool = True
        ordering: list[str] = ["updated_at"]

    @override
    def __str__(self) -> str:
        return super().__str__()

    @override
    def save(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        _ = structlog.contextvars.bind_contextvars(
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
        logger.debug(
            "Saving object...",
        )
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
        logger.debug(
            "Saved.",
        )
        structlog.contextvars.unbind_contextvars("created_at", "updated_at")


class UserCreatedObject(CommonObject):
    author: models.ForeignKey[User] = models.ForeignKey(
        User, on_delete=models.CASCADE
    )

    class Meta(CommonObject.Meta):
        abstract: bool = True


class Bulletin(CommonObject):
    title: models.TextField[str, str] = title_field()


class BulletinPostManager(models.Manager["BulletinPost"]):
    def create_classified(
        self,
        title: str,
        body: str,
        author: User,
        bulletin: Bulletin,
        user_key: bytes,
    ) -> "BulletinPost":
        wrapped_post_key, post_key_nonce = PostEncryptionKey.create_key(
            user_key
        )
        post = BulletinPost.objects.create(
            title=title,
            body=body,
            author=author,
            bulletin=bulletin,
            is_classified=True,
        )
        logger.debug("Post created.")
        author.save()
        logger.debug("Author saved.")
        post_key_obj = PostEncryptionKey.objects.create(
            post=post, wrapped_key=wrapped_post_key, key_nonce=post_key_nonce
        )
        title_enc, title_nonce = post_key_obj.encrypt(title, user_key)
        body_enc, body_nonce = post_key_obj.encrypt(body, user_key)
        post.title = title_enc
        post.title_nonce = title_nonce
        post.body = body_enc
        post.body_nonce = body_nonce
        post.save()
        return post

    def update_classified(
        self, pk: int, title: str, body: str, user_key: bytes
    ) -> "BulletinPost":
        post = BulletinPost.objects.get(pk=pk)
        post_key = PostEncryptionKey.objects.get(post=post)
        title_enc, title_nonce = post_key.encrypt(title, user_key)
        body_enc, body_nonce = post_key.encrypt(body, user_key)
        post.title = title_enc
        post.title_nonce = title_nonce
        post.body = body_enc
        post.body_nonce = body_nonce
        post.save()
        return post


class BulletinPost(UserCreatedObject):
    title: models.TextField[str, str] = title_field()
    title_nonce: OptionalByteField = models.BinaryField(null=True)
    body: models.TextField[str, str] = body_field()
    body_nonce: OptionalByteField = models.BinaryField(null=True)

    is_classified: models.BooleanField[bool, bool] = models.BooleanField(
        default=False
    )

    bulletin: models.ForeignKey[Bulletin] = models.ForeignKey(
        Bulletin, on_delete=models.CASCADE
    )

    objects: BulletinPostManager = BulletinPostManager()

    def decrypted(self, password: str) -> "BulletinPost":
        self.title = self.decrypt_title(password)
        self.body = self.decrypt_body(password)
        return self

    def decrypted_as(
        self, claimant: User, password: str
    ) -> "BulletinPost | None":
        title = self.decrypt_title_as(claimant, password)
        body = self.decrypt_body_as(claimant, password)
        if title is None or body is None:
            return None

        self.title = title
        self.body = body
        return self

    def decrypt_title(self, password: str) -> str:
        if not self.is_classified:
            return self.title
        assert self.title_nonce is not None
        post_key = PostEncryptionKey.objects.get(post=self)
        user_key = UserEncryptionKey.objects.get(user=self.author)
        user_key = user_key.get_user_key(password)
        plaintext = post_key.decrypt(self.title, self.title_nonce, user_key)
        return plaintext.decode()

    def decrypt_body(self, password: str) -> str:
        if not self.is_classified:
            return self.body
        assert self.body_nonce is not None
        post_key = PostEncryptionKey.objects.get(post=self)
        user_key = UserEncryptionKey.objects.get(user=self.author)
        user_key = user_key.get_user_key(password)
        plaintext = post_key.decrypt(self.body, self.body_nonce, user_key)
        return plaintext.decode()

    def decrypt_title_as(self, claimant: User, password: str) -> str | None:
        if not self.is_classified:
            return self.title
        assert self.title_nonce is not None
        author_key = UserEncryptionKey.objects.get(user=self.author)
        claimant_key = UserEncryptionKey.objects.get(user=claimant)
        shared_post_access = SharedPostAccess.objects.get(
            post=self, user=claimant
        )
        claimant_key_value = claimant_key.get_user_key(password)
        claimant_private_key = claimant_key.retrieve_private_key(
            claimant_key_value
        )
        post_key = shared_post_access.unwrap(
            author_key.public_key, claimant_private_key
        )
        plaintext = decrypt_encoded_content(
            self.title, post_key, self.title_nonce
        )
        return plaintext.decode()

    def decrypt_body_as(self, claimant: User, password: str) -> str | None:
        log = logger.bind(comment_id=self.pk, claimant=claimant.username)
        if not self.is_classified:
            return self.body
        assert self.body_nonce is not None
        author_key = UserEncryptionKey.objects.get(user=self.author)
        claimant_key = UserEncryptionKey.objects.get(user=claimant)
        try:
            shared_post_access = SharedPostAccess.objects.get(
                post=self, user=claimant
            )
            claimant_key_value = claimant_key.get_user_key(password)
            claimant_private_key = claimant_key.retrieve_private_key(
                claimant_key_value
            )
            post_key = shared_post_access.unwrap(
                author_key.public_key, claimant_private_key
            )
            plaintext = decrypt_encoded_content(
                self.body, post_key, self.body_nonce
            )
            return plaintext.decode()
        except SharedPostAccess.DoesNotExist:
            log.warning("Unauthorized comment decryption attempt.")
            return None
        except ValueError:
            log.warning("Password failure on comment decryption.")
            return None


class CommentManager(models.Manager["Comment"]):
    def create_classified(
        self,
        body: str,
        commenter: User,
        post: BulletinPost,
        user_key: bytes,
    ) -> "Comment":
        shared_post_key = SharedPostAccess.objects.get(
            post=post, user=commenter
        )
        commenter_key_obj = UserEncryptionKey.objects.get(user=commenter)
        poster_key_obj = UserEncryptionKey.objects.get(user=post.author)
        commenter_private_key = commenter_key_obj.retrieve_private_key(user_key)
        post_key = shared_post_key.unwrap(
            poster_key_obj.public_key, commenter_private_key
        )
        body_enc, body_nonce = shared_post_key.encrypt(body, post_key)
        comment = Comment.objects.create(
            body=body_enc,
            body_nonce=body_nonce,
            author=commenter,
            bulletin_post=post,
        )
        comment.save()
        return comment

    def update_classified(
        self, pk: int, body: str, user_key: bytes
    ) -> "Comment":
        comment = Comment.objects.get(pk=pk)
        shared_post_key = SharedPostAccess.objects.get(
            post=comment.bulletin_post, user=comment.author
        )
        commenter_key_obj = UserEncryptionKey.objects.get(user=comment.author)
        poster_key_obj = UserEncryptionKey.objects.get(
            user=comment.bulletin_post.author
        )
        commenter_private_key = commenter_key_obj.retrieve_private_key(user_key)
        post_key = unwrap_shared_key(
            shared_post_key.wrapped_key,
            shared_post_key.key_nonce,
            commenter_private_key,
            poster_key_obj.public_key,
        )
        body_enc, body_nonce = shared_post_key.encrypt(body, post_key)
        comment.body = body_enc
        comment.body_nonce = body_nonce
        comment.save()

        return comment


class Comment(UserCreatedObject):
    bulletin_post: models.ForeignKey[BulletinPost] = models.ForeignKey(
        BulletinPost, on_delete=models.CASCADE
    )
    body: models.TextField[str, str] = body_field()
    body_nonce: OptionalByteField = models.BinaryField(null=True)

    objects: CommentManager = CommentManager()

    def decrypted(self, claimant: User, password: str) -> "Comment | None":
        body = self.decrypt_body_as(claimant, password)
        if body is None:
            return None
        self.body = body
        return self

    def decrypt_body_as(self, claimant: User, password: str) -> str | None:
        log = logger.bind(comment_id=self.pk, claimant=claimant.username)
        if not self.bulletin_post.is_classified:
            return self.body
        assert self.body_nonce is not None
        author_key = UserEncryptionKey.objects.get(
            user=self.bulletin_post.author
        )
        claimant_key = UserEncryptionKey.objects.get(user=claimant)
        try:
            shared_post_access = SharedPostAccess.objects.get(
                post=self.bulletin_post, user=claimant
            )
            claimant_key_value = claimant_key.get_user_key(password)
            claimant_private_key = claimant_key.retrieve_private_key(
                claimant_key_value
            )
            post_key = shared_post_access.unwrap(
                author_key.public_key, claimant_private_key
            )
            plaintext = shared_post_access.decrypt(
                self.body, self.body_nonce, post_key
            )
            return plaintext.decode()
        except SharedPostAccess.DoesNotExist:
            log.warning("Unauthorized comment decryption attempt.")
            return None
        except ValueError:
            log.warning("Password failure on comment decryption.")
            return None


class PostEncryptionKey(EncryptionKey):
    """Per-post symmetric key, wrapped by author's master key"""

    post: models.OneToOneField[BulletinPost] = models.OneToOneField(
        BulletinPost, on_delete=models.CASCADE
    )


class SharedPostAccess(EncryptionKey):
    """Allows other users to access a post's key"""

    post: models.ForeignKey[BulletinPost] = models.ForeignKey(
        BulletinPost, on_delete=models.CASCADE
    )
    user: models.ForeignKey[User] = models.ForeignKey(
        User, on_delete=models.CASCADE
    )

    class Meta(EncryptionKey.Meta):
        unique_together: list[str] = ["post", "user"]

    @classmethod
    def create_for_user(
        cls,
        post: "BulletinPost",
        recipient: User,
        sender: User,
        sender_user_key: bytes,
    ) -> "SharedPostAccess":
        post_key_obj = PostEncryptionKey.objects.get(post=post)
        post_key = post_key_obj._retrieve_key(sender_user_key)
        recipient_key_obj = UserEncryptionKey.objects.get(user=recipient)
        sender_key_obj = UserEncryptionKey.objects.get(user=sender)
        sender_private_key = sender_key_obj.retrieve_private_key(
            sender_user_key
        )
        wrapped_key, nonce = wrap_shared_key(
            post_key, sender_private_key, recipient_key_obj.public_key
        )
        return cls.objects.create(
            post=post,
            user=recipient,
            wrapped_key=wrapped_key,
            key_nonce=nonce,
        )

    def unwrap(
        self, sender_public_key: bytes, recipient_private_key: bytes
    ) -> bytes:
        return unwrap_shared_key(
            self.wrapped_key,
            self.key_nonce,
            sender_public_key,
            recipient_private_key,
        )

    @override
    def encrypt(self, plaintext: str, wrapper_key: bytes) -> tuple[str, bytes]:
        ciphertext, nonce = encrypt_content(plaintext.encode(), wrapper_key)
        encoded_ciphertext = base64.b64encode(ciphertext).decode()
        return encoded_ciphertext, nonce

    @override
    def decrypt(
        self, encoded_ciphertext: str, nonce: bytes, wrapper_key: bytes
    ) -> bytes:
        plaintext = decrypt_encoded_content(
            encoded_ciphertext, wrapper_key, nonce
        )
        return plaintext
