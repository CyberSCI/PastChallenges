# Step 1: Bug Fixes & Infrastructure

## 1a. Fix `list_comments` filter bug

**File:** `bulletin/views.py`, line 160

Change:
```python
comments = Comment.objects.filter(bulletin=bulletin_post)
```
To:
```python
comments = Comment.objects.filter(bulletin_post=bulletin_post)
```

## 1b. Register `CommentViewSet` in URLs

**File:** `bulletin/urls.py`

Add:
```python
router.register(r"comments", CommentViewSet, basename="comments")
```

Import `CommentViewSet` if not already imported.

## 1c. Add `decrypted` action to `CommentViewSet`

**File:** `bulletin/views.py`

Add to `CommentViewSet`:
```python
@action(detail=True, methods=["POST"], url_path="decrypted", url_name="decrypt_comment")
def decrypted(self, request: Request, pk: int | None = None) -> Response:
    comment = self.get_object()
    password = request.data.get("password", "")
    decrypted_comment = comment.decrypted(request.user, password)
    if decrypted_comment is None:
        return Response(status=HTTPStatus.FORBIDDEN)
    data = CommentSerializer(decrypted_comment).data
    return Response(data)
```
