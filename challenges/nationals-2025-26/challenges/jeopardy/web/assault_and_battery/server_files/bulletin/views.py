from http import HTTPStatus
from typing import Any, TypeVar, override

import structlog
from django.db.models import QuerySet
from knox import auth as knox_auth
from rest_framework import authentication as drf_authentication
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from bulletin.models import Bulletin, BulletinPost, Comment
from bulletin.serializers import (
    BulletinPostSerializer,
    BulletinSerializer,
    CommentSerializer,
    SharePostAccessSerializer,
)
from shared.types import AuthenticationClasses, PermissionsClasses

logger = structlog.stdlib.get_logger("reclaimer_central.bulletin")

TUserCreated = TypeVar("TUserCreated", bound=BulletinPost | Comment)

ForbiddenResponse = Response(
    status=HTTPStatus.FORBIDDEN,
    data={"message": "DO NOT INTERFERE."},
)


class UserCreatedModelViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
    UpdateModelMixin,
    GenericViewSet[TUserCreated],
):
    permission_classes: PermissionsClasses = (permissions.IsAuthenticated,)
    authentication_classes: AuthenticationClasses = [
        drf_authentication.SessionAuthentication,
        knox_auth.TokenAuthentication,
    ]

    @override
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if request.user.pk != self.get_object().author.pk:
            return ForbiddenResponse
        return super().update(request, *args, **kwargs)

    @override
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if request.user.pk != self.get_object().author.pk:
            return ForbiddenResponse
        return super().destroy(request, *args, **kwargs)


class BulletinViewSet(ModelViewSet[Bulletin]):
    queryset: QuerySet[Bulletin] = Bulletin.objects.all()
    serializer_class: type[BulletinSerializer] = BulletinSerializer
    authentication_classes: AuthenticationClasses = [
        drf_authentication.SessionAuthentication,
        knox_auth.TokenAuthentication,
    ]

    @override
    def get_permissions(self) -> list[permissions.BasePermission]:
        if self.action in ("list", "retrieve", "posts"):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    def create_post(self, request: Request, pk: int | None = None) -> Response:
        post_serializer = BulletinPostSerializer(
            data=request.data,
            context={"request": request},
        )
        if not post_serializer.is_valid():
            return Response(
                post_serializer.errors, status=HTTPStatus.BAD_REQUEST
            )

        bulletin_post = post_serializer.create(post_serializer.validated_data)
        response_data = post_serializer.to_representation(bulletin_post)
        return Response(data=response_data, status=HTTPStatus.CREATED)

    @action(
        detail=True,
        methods=["GET", "POST"],
        url_path="posts",
        url_name="bulletin_posts",
    )
    def posts(self, request: Request, pk: int | None = None) -> Response:
        if request.method == "GET":
            return self.list_posts(request, pk)

        if request.method == "POST":
            return self.create_post(request, pk)

        return Response(status=HTTPStatus.METHOD_NOT_ALLOWED)

    def list_posts(self, request: Request, pk: int | None = None) -> Response:
        bulletin = self.get_object()
        bulletin_posts = BulletinPost.objects.filter(bulletin=bulletin)
        response_data = BulletinPostSerializer(bulletin_posts, many=True).data
        return Response(data=response_data)


class BulletinPostViewSet(UserCreatedModelViewSet[BulletinPost]):
    queryset: QuerySet[BulletinPost] = BulletinPost.objects.all()
    serializer_class: type[BulletinPostSerializer] = BulletinPostSerializer

    @action(
        detail=True,
        methods=["POST"],
        url_path="decrypted",
        url_name="decrypt_post",
    )
    def decrypted(self, request: Request, pk: int | None = None) -> Response:
        context = {"request": request}
        bulletin_post = self.get_object()
        if not bulletin_post.is_classified:
            data = BulletinPostSerializer(bulletin_post, context=context).data
            return Response(data)

        password = request.data.get("password", "")
        if request.user.pk != bulletin_post.author.pk:
            decrypted_post = bulletin_post.decrypted_as(
                request.user,  # pyright: ignore
                password,
            )
            data = BulletinPostSerializer(decrypted_post, context=context).data
            return Response(data)

        decrypted_post = bulletin_post.decrypted(password)
        data = BulletinPostSerializer(decrypted_post, context=context).data
        return Response(data)

    @action(
        detail=True,
        methods=["GET", "POST"],
        url_path="comments",
        url_name="post_comments",
    )
    def comments(self, request: Request, pk: int | None = None) -> Response:
        if request.method == "GET":
            return self.list_comments(request, pk)
        if request.method == "POST":
            return self.create_comment(request, pk)
        return Response(status=HTTPStatus.METHOD_NOT_ALLOWED)

    def list_comments(
        self, request: Request, pk: int | None = None
    ) -> Response:
        bulletin_post = self.get_object()
        comments = Comment.objects.filter(bulletin_post=bulletin_post)
        response_data = CommentSerializer(comments, many=True).data
        return Response(data=response_data)

    def create_comment(
        self, request: Request, pk: int | None = None
    ) -> Response:
        comment_serializer = CommentSerializer(
            data=request.data,
            context={"request": request},
        )
        if not comment_serializer.is_valid():
            return Response(
                comment_serializer.errors, status=HTTPStatus.BAD_REQUEST
            )

        comment = comment_serializer.create(comment_serializer.validated_data)
        response_data = comment_serializer.to_representation(comment)
        return Response(data=response_data, status=HTTPStatus.CREATED)

    @action(detail=True, methods=["POST"], url_path="share", url_name="share")
    def share(self, request: Request, pk: int | None = None) -> Response:
        post = self.get_object()
        serializer = SharePostAccessSerializer(
            data=request.data,
            context={"request": request, "post": post},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTPStatus.BAD_REQUEST)
        serializer.create(serializer.validated_data)
        return Response(status=HTTPStatus.NO_CONTENT)


class CommentViewSet(UserCreatedModelViewSet[Comment]):
    queryset: QuerySet[Comment] = Comment.objects.all()
    serializer_class: type[CommentSerializer] = CommentSerializer

    @action(
        detail=True,
        methods=["POST"],
        url_path="decrypted",
        url_name="decrypt_comment",
    )
    def decrypted(self, request: Request, pk: int | None = None) -> Response:
        comment = self.get_object()
        if not comment.bulletin_post.is_classified:
            data = CommentSerializer(comment).data
            return Response(data)

        password = request.data.get("password", "")
        decrypted_comment = comment.decrypted(
            request.user,  # pyright: ignore
            password,
        )
        if decrypted_comment is None:
            return Response(status=HTTPStatus.FORBIDDEN)
        data = CommentSerializer(decrypted_comment).data
        return Response(data)
