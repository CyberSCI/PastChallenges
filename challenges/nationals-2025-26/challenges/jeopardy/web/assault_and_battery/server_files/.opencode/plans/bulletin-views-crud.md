# Plan: Round Out Bulletin Views

## Goal

Complete CRUD endpoints for `BulletinPost` and `Comment`, add nested comment
access under posts, add post-sharing, and wire up the URL router.

## URL Structure (all under `api/bulletins/`)

| Method | URL | Action |
|---|---|---|
| GET | `/api/bulletins/<pk>/posts/` | list posts on bulletin (existing) |
| POST | `/api/bulletins/<pk>/posts/` | create post on bulletin (existing) |
| GET | `/api/bulletins/<pk>/posts/<post_pk>/` | get single post (new) |
| GET | `/api/bulletins/posts/<pk>/` | retrieve post |
| PATCH | `/api/bulletins/posts/<pk>/` | update post (author only) |
| DELETE | `/api/bulletins/posts/<pk>/` | delete post (author only) |
| GET | `/api/bulletins/posts/<pk>/comments/` | list comments on post |
| POST | `/api/bulletins/posts/<pk>/comments/` | create comment on post |
| POST | `/api/bulletins/posts/<pk>/share/` | grant shared access |
| GET | `/api/bulletins/comments/<pk>/` | retrieve comment |
| PATCH | `/api/bulletins/comments/<pk>/` | update comment (author only) |
| DELETE | `/api/bulletins/comments/<pk>/` | delete comment (author only) |

## Changes

### `bulletin/urls.py`

Register `BulletinPostViewSet` and `CommentViewSet` on the existing router:

```python
from bulletin.views import BulletinPostViewSet, BulletinViewSet, CommentViewSet

router = DefaultRouter()
router.register(r"", BulletinViewSet, basename="bulletin")
router.register(r"posts", BulletinPostViewSet, basename="post")
router.register(r"comments", CommentViewSet, basename="comment")
```

### `bulletin/views.py`

#### 1. Add imports

```python
from django.shortcuts import get_object_or_404
from bulletin.serializers import SharePostAccessSerializer  # already in serializers.py
```

#### 2. `BulletinViewSet` — add `post_detail` action

```python
@action(
    detail=True,
    methods=["GET"],
    url_path=r"posts/(?P<post_pk>[^/.]+)",
    url_name="post-detail",
)
def post_detail(self, request: Request, pk: int | None = None, post_pk: int | None = None) -> Response:
    bulletin = self.get_object()
    post = get_object_or_404(BulletinPost, pk=post_pk, bulletin=bulletin)
    return Response(BulletinPostSerializer(post).data)
```

#### 3. `BulletinPostViewSet` — add comment actions + share action

```python
@action(detail=True, methods=["GET", "POST"], url_path="comments", url_name="comments")
def comments(self, request: Request, pk: int | None = None) -> Response:
    if request.method == "GET":
        return self.list_comments(request, pk)
    if request.method == "POST":
        return self.create_comment(request, pk)
    return Response(status=HTTPStatus.METHOD_NOT_ALLOWED)

def list_comments(self, request: Request, pk: int | None = None) -> Response:
    post = self.get_object()
    comments = Comment.objects.filter(bulletin_post=post)
    return Response(CommentSerializer(comments, many=True).data)

def create_comment(self, request: Request, pk: int | None = None) -> Response:
    post = self.get_object()
    data = {**request.data, "bulletin_post": post.pk}
    comment_serializer = CommentSerializer(data=data, context={"request": request})
    if not comment_serializer.is_valid():
        return Response(comment_serializer.errors, status=HTTPStatus.BAD_REQUEST)
    comment = comment_serializer.create(comment_serializer.validated_data)
    return Response(CommentSerializer(comment).data, status=HTTPStatus.CREATED)

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
```

### `bulletin/serializers.py` — minimal fix

`CommentSerializer.Meta.read_only_fields` currently lists `bulletin_post` and `body`
as read-only. `bulletin_post` must be writable for create to work. Remove it from
`read_only_fields`. `body` should also be writable for create/update.

Remove from `read_only_fields`:
- `"body"`
- `"bulletin_post"`

Also add `validate` to set `author` from request context (mirrors `BulletinPostSerializer`):

```python
@override
def validate(self, attrs: Any) -> Any:
    attrs["author"] = self.context["request"].user
    return super().validate(attrs)
```

> Note: `BulletinPostSerializer.create` references `user` (undefined) instead of
> `validated_data["author"]` on line 74. This is a pre-existing bug — not fixing
> here unless asked.
