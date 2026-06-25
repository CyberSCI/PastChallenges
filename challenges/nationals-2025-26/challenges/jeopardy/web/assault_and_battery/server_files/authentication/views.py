from http import HTTPStatus
from typing import override

import structlog
from django.contrib.auth import login
from knox.views import LoginView as KnoxLoginView
from rest_framework import permissions, serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.serializers import RegisterSerializer

logger = structlog.stdlib.get_logger("reclaimer_central.authentication")

PermissionsClasses = tuple[type[permissions.BasePermission], ...]


class LoginView(KnoxLoginView):
    permission_classes: PermissionsClasses = (permissions.AllowAny,)

    @override
    def post(self, request: Request, format: None = None) -> Response:
        serializer = AuthTokenSerializer(data=request.data)
        try:
            _ = structlog.contextvars.bind_contextvars(
                username=serializer.initial_data.get("username")
            )
            _ = serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            logger.warn("Invalid login credentials")
            structlog.contextvars.unbind_contextvars("username")
            raise e
        except Exception as e:
            logger.exception("Unknown exception.")
            structlog.contextvars.unbind_contextvars("username")
            raise e
        user = serializer.validated_data.get("user", None)
        login(request, user)
        structlog.contextvars.unbind_contextvars("username")
        return super().post(request, format=None)


class RegisterView(APIView):
    permission_classes: PermissionsClasses = (permissions.AllowAny,)

    def post(self, request: Request, format: None = None):
        serializer = RegisterSerializer(data=request.data)
        try:
            _ = structlog.contextvars.bind_contextvars(
                username=serializer.initial_data.get("username")
            )
            _ = serializer.is_valid(raise_exception=True)
            user = serializer.save()
            login(request, user)
        except Exception as e:
            logger.warning("Unable to save user", error=str(e))
            structlog.contextvars.unbind_contextvars("username")
            return Response(
                data={"message": "Could not complete registration."},
                status=HTTPStatus.BAD_REQUEST,
            )

        structlog.contextvars.unbind_contextvars("username")
        return Response(
            data={"message": "User registered successfully."},
            status=HTTPStatus.CREATED,
        )
