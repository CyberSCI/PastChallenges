from typing import Any, override

import structlog
from django.contrib.auth.models import User
from rest_framework import serializers

from authentication.models import UserEncryptionKey
from bulletin.models import Bulletin, BulletinPost, Comment, SharedPostAccess

logger = structlog.stdlib.get_logger("reclaimer_central.bulletin")


class BulletinSerializer(serializers.ModelSerializer[Bulletin]):
    class Meta:
        model: type[Bulletin] = Bulletin
        fields: list[str] = ["id", "title", "created_at", "updated_at"]
        read_only_fields: list[str] = [
            "id",
            "created_at",
            "updated_at",
            "bulletin_post_set",
        ]


class BulletinPostSerializer(serializers.ModelSerializer[BulletinPost]):
    password: serializers.CharField = serializers.CharField(
        write_only=True, required=False
    )

    class Meta:
        model: type[BulletinPost] = BulletinPost
        fields: list[str] = [
            # keep-sorted start
            "author",
            "body",
            "body_nonce",
            "bulletin",
            "created_at",
            "id",
            "is_classified",
            "password",
            "title",
            "title_nonce",
            "updated_at",
            # keep-sorted end
        ]
        read_only_fields: list[str] = [
            # keep-sorted start
            "author",
            "body_nonce",
            "created_at",
            "id",
            "title_nonce",
            "updated_at",
            # keep-sorted end
        ]

    @override
    def validate(self, attrs: Any) -> Any:
        author = self.context["request"].user
        attrs["author"] = author
        return super().validate(attrs)

    @override
    def create(self, validated_data: dict[str, Any]) -> BulletinPost:
        password = validated_data.pop("password", None)
        is_classified = validated_data.get("is_classified", False)
        if not is_classified:
            return BulletinPost.objects.create(
                title=validated_data["title"],
                body=validated_data["body"],
                author=validated_data["author"],
                bulletin=validated_data["bulletin"],
            )

        if not password:
            raise serializers.ValidationError(
                "Password required for classified posts."
            )
        user_key = UserEncryptionKey.objects.get(
            user=validated_data["author"]
        ).get_user_key(password)
        post = BulletinPost.objects.create_classified(
            title=validated_data["title"],
            body=validated_data["body"],
            author=validated_data["author"],
            bulletin=validated_data["bulletin"],
            user_key=user_key,
        )
        return post

    @override
    def update(
        self, instance: BulletinPost, validated_data: Any
    ) -> BulletinPost:
        return super().update(instance, validated_data)


class CommentSerializer(serializers.ModelSerializer[Comment]):
    password: serializers.CharField = serializers.CharField(
        write_only=True, required=False
    )

    class Meta:
        model: type[Comment] = Comment
        fields: list[str] = [
            # keep-sorted start
            "author",
            "body",
            "body_nonce",
            "bulletin_post",
            "created_at",
            "id",
            "password",
            "updated_at",
            # keep-sorted end
        ]
        read_only_fields: list[str] = [
            # keep-sorted start
            "author",
            "body_nonce",
            "created_at",
            "id",
            "updated_at",
            # keep-sorted end
        ]

    @override
    def create(self, validated_data: dict[str, Any]) -> Comment:
        password = validated_data.pop("password", None)
        user = self.context["request"].user
        post = validated_data["bulletin_post"]
        validated_data["author"] = user
        if not post.is_classified:
            return Comment.objects.create(**validated_data)

        if not password:
            raise serializers.ValidationError(
                "Password required to comment on classified posts."
            )
        user_key = UserEncryptionKey.objects.get(user=user).get_user_key(
            password
        )
        return Comment.objects.create_classified(
            body=validated_data["body"],
            commenter=user,
            post=post,
            user_key=user_key,
        )

    @override
    def update(self, instance: Comment, validated_data: Any) -> Comment:
        return super().update(instance, validated_data)


class SharePostAccessSerializer(serializers.Serializer[SharedPostAccess]):
    recipient_username: serializers.CharField = serializers.CharField()
    password: serializers.CharField = serializers.CharField(write_only=True)

    @override
    def validate(self, attrs: dict[str, Any]):
        request = self.context["request"]
        post = self.context["post"]
        if not post.is_classified:
            raise serializers.ValidationError(
                "Post is not classified, nothing to share."
            )
        _ = structlog.contextvars.bind_contextvars(
            post=post.pk,
            author=post.author.pk,
            username=request.user.username,
            recipient_username=attrs["recipient_username"],
        )
        logger.debug(
            "Validating share request",
            **attrs,
        )
        if post.author.pk != request.user.pk:
            logger.warn("Unauthorized share attempt.")
            raise serializers.ValidationError(
                "Only the post author can share access."
            )
        try:
            attrs["recipient"] = User.objects.get(
                username=attrs["recipient_username"]
            )
        except User.DoesNotExist as e:
            raise serializers.ValidationError(
                "Recipient user not found."
            ) from e
        if SharedPostAccess.objects.filter(
            post=post, user=attrs["recipient"]
        ).exists():
            raise serializers.ValidationError("Access already granted.")
        return attrs

    @override
    def create(self, validated_data: dict[str, Any]) -> SharedPostAccess:
        password = validated_data.pop("password", None)
        post: BulletinPost = self.context["post"]
        user_key = UserEncryptionKey.objects.get(user=post.author).get_user_key(
            password
        )
        return SharedPostAccess.create_for_user(
            post=post,
            recipient=validated_data["recipient"],
            sender=post.author,
            sender_user_key=user_key,
        )
