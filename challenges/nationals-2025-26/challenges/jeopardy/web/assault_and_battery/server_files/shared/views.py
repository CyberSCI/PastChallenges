from knox import auth as knox_auth
from rest_framework import authentication as drf_authentication
from rest_framework import permissions
from rest_framework.views import APIView

from shared.types import AuthenticationClasses, PermissionsClasses


class AuthenticatedApiView(APIView):
    authentication_classes: AuthenticationClasses = [
        drf_authentication.SessionAuthentication,
        knox_auth.TokenAuthentication,
    ]
    permission_classes: PermissionsClasses = (permissions.IsAuthenticated,)
