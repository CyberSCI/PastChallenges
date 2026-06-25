from django.db import models
from rest_framework import authentication as drf_authentication
from rest_framework import permissions

PermissionsClasses = tuple[type[permissions.BasePermission], ...]
AuthenticationClasses = list[type[drf_authentication.BaseAuthentication]]

ByteField = models.BinaryField[bytes, bytes]
OptionalByteField = models.BinaryField[bytes | None, bytes | None]
