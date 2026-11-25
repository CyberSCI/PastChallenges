import time
from functools import wraps

import jwt
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse

from forum.models import User
from forum.policies import is_admin


def issue_token(user: User) -> str:
    now = int(time.time())
    return jwt.encode(
        {"sub": str(user.pk), "iat": now, "exp": now + settings.JWT_TTL_SECONDS, "iss": settings.JWT_ISSUER},
        settings.JWT_SIGNING_KEY,
        algorithm="HS256",
    )


def authenticated_user(request: HttpRequest):
    token = request.headers.get("X-API-Token", "")
    if not token:
        return None, False
    if any(character.isspace() for character in token):
        return None, True
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SIGNING_KEY,
            algorithms=["HS256"],
            issuer=settings.JWT_ISSUER,
            options={"require": ["sub", "iat", "exp", "iss"]},
        )
        user = User.objects.get(pk=payload["sub"], is_active=True, approval_status=User.ApprovalStatus.APPROVED)
    except (jwt.PyJWTError, User.DoesNotExist, ValueError, TypeError):
        return None, True
    return user, False


def markdown_error(status: int, message: str) -> HttpResponse:
    return HttpResponse(
        f"# Request failed\n\n{message}\n",
        status=status,
        content_type="text/markdown; charset=utf-8",
    )


def api_token_required(admin=False, markdown=False):
    def decorate(view):
        @wraps(view)
        def wrapped(request: HttpRequest, *args, **kwargs):
            user, _invalid = authenticated_user(request)
            if user is None:
                if markdown:
                    return markdown_error(401, "A valid API token is required.")
                return JsonResponse({"error": "A valid API token is required."}, status=401)
            if admin and not is_admin(user):
                if markdown:
                    return markdown_error(403, "Administrator access required.")
                return JsonResponse({"error": "Administrator access required."}, status=403)
            request.user = user
            return view(request, *args, **kwargs)

        return wrapped

    return decorate


def optional_markdown_user(request):
    if not request.headers.get("X-API-Token"):
        return None, None
    user, invalid = authenticated_user(request)
    if invalid or user is None:
        return None, markdown_error(401, "A valid API token is required.")
    return user, None


def json_body(request):
    if request.content_type != "application/json":
        raise ValueError("Content-Type must be application/json.")
    if len(request.body) > settings.MAX_JSON_BODY_BYTES:
        raise OverflowError("Request body is too large.")
    try:
        import json

        payload = json.loads(request.body)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("Request body must contain valid JSON.") from exc
    if not isinstance(payload, dict):
        raise ValueError("JSON request body must be an object.")
    return payload


def json_error(message: str, status: int):
    return JsonResponse({"error": message}, status=status)