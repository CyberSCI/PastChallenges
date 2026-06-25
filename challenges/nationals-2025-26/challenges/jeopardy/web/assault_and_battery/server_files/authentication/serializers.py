from typing import override

import structlog
from django.contrib.auth.models import User
from rest_framework import serializers

from authentication.models import UserEncryptionKey

logger = structlog.stdlib.get_logger("reclaimer_central.authentication")


class RegisterSerializer(serializers.Serializer[User | None]):
    username: serializers.CharField = serializers.CharField()
    password: serializers.CharField = serializers.CharField()

    # TODO: Add MFA just to spice things up

    @override
    def create(self, validated_data: dict[str, str]):

        username = validated_data["username"]
        password = validated_data["password"]
        try:
            _ = User.objects.get(username=username)

            raise serializers.ValidationError("User already exists.")

        except User.DoesNotExist:
            pass

        except serializers.ValidationError as e:
            logger.warning("User already exists.")
            raise e

        try:
            user = User.objects.create_user(
                username=username, password=password
            )
            UserEncryptionKey.setup(user, password)
            logger.info("User created", username=user.username)
            return user
        except Exception:
            logger.exception("Exception occurred when creating user.")

    def create_admin(self, validated_data: dict[str, str]):
        username = validated_data["username"]
        password = validated_data["password"]
        try:
            _ = User.objects.get(username=username)
            raise serializers.ValidationError("User already exists.")

        except User.DoesNotExist:
            pass

        except serializers.ValidationError as e:
            logger.warning("User already exists.")
            raise e

        try:
            user = User.objects.create_user(
                username=username, password=password, is_staff=True
            )
            UserEncryptionKey.setup(user, password)
            logger.info("User created", username=user.username)
            return user
        except Exception:
            logger.exception("Exception occurred when creating user.")
