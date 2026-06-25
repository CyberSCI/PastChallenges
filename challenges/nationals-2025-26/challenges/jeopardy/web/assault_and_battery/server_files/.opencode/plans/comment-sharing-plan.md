## Plan: Bulletin Comment Sharing

### Overview

The core problem: to write encrypted comments on a classified post, a user needs the post's symmetric key — but that key is only directly accessible to the post's author. `SharedPostAccess` is the mechanism for sharing it, but nothing creates those records yet, and `Comment.encrypt()` is a stub.

The solution uses **X25519 ECDH** for key-sharing: the author unwraps the post key with their own `master_key`, then re-wraps it for the recipient using ECDH with the recipient's public key. The recipient unwraps it using their private key (recoverable via their own password).

---

### Key Hierarchy for Comment Sharing

```
Author's password → PBKDF2 → password_key → unwrap master_key
   master_key → unwrap PostEncryptionKey → post_key (32 bytes)

post_key re-wrapped for recipient:
  ephemeral X25519 keypair generated
  ECDH(ephemeral_private, recipient.public_key) → shared_secret
  encrypt_content(post_key, shared_secret) → (wrapped_key, key_nonce)
  SharedPostAccess(wrapped_key, key_nonce, ephemeral_public_key) saved

Recipient decrypts:
  recipient's password → PBKDF2 → password_key → unwrap master_key
  master_key → unwrap private_key
  ECDH(recipient_private, ephemeral_public_key) → shared_secret
  decrypt_content(wrapped_key, shared_secret, key_nonce) → post_key
```

---

### Files Changed

#### 1. `crypto/vault.py` — Add ECDH key-wrapping helpers

Add two functions:

```python
def wrap_key_for_recipient(post_key: bytes, recipient_public_key_bytes: bytes) -> tuple[bytes, bytes, bytes]:
    """
    ECDH-wraps post_key for a recipient using their X25519 public key.
    Returns (wrapped_key, nonce, ephemeral_public_key_bytes).
    """
    ephemeral_private = X25519PrivateKey.generate()
    ephemeral_public = ephemeral_private.public_key()
    recipient_public = X25519PublicKey.from_public_bytes(recipient_public_key_bytes)
    shared_secret = ephemeral_private.exchange(recipient_public)
    wrapped_key, nonce = encrypt_content(post_key, shared_secret)
    return wrapped_key, nonce, ephemeral_public.public_bytes_raw()


def unwrap_key_from_ecdh(wrapped_key: bytes, nonce: bytes, ephemeral_public_key_bytes: bytes, recipient_private_key_bytes: bytes) -> bytes:
    """
    Recovers post_key using recipient's private key and the stored ephemeral public key.
    """
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey as _PK
    recipient_private = _PK.from_private_bytes(recipient_private_key_bytes)
    ephemeral_public = X25519PublicKey.from_public_bytes(ephemeral_public_key_bytes)
    shared_secret = recipient_private.exchange(ephemeral_public)
    return decrypt_content(wrapped_key, shared_secret, nonce)
```

---

#### 2. `bulletin/models.py` — Three changes

**A) Add `ephemeral_public_key` field to `SharedPostAccess`**

This stores the ephemeral X25519 public key needed for ECDH unwrapping by the recipient.

```python
class SharedPostAccess(EncryptionKey):
    """Allows other users to access a post's key"""

    post = models.ForeignKey(BulletinPost, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ephemeral_public_key: models.BinaryField[bytes] = models.BinaryField()

    class Meta(EncryptionKey.Meta):
        unique_together = ["post", "user"]

    @classmethod
    def create_for_user(
        cls,
        post: "BulletinPost",
        recipient: User,
        grantor_master_key: bytes,
    ) -> "SharedPostAccess":
        post_key_obj = PostEncryptionKey.objects.get(post=post)
        post_key = post_key_obj._retrieve_key(grantor_master_key)
        recipient_key_obj = UserEncryptionKey.objects.get(user=recipient)
        wrapped_key, nonce, ephemeral_pub = wrap_key_for_recipient(
            post_key, bytes(recipient_key_obj.public_key)
        )
        return cls.objects.create(
            post=post,
            user=recipient,
            wrapped_key=wrapped_key,
            key_nonce=nonce,
            ephemeral_public_key=ephemeral_pub,
        )
```

**B) Complete `CommentManager.create_classified()`**

```python
def create_classified(self, body: str, author: User, post: BulletinPost, master_key: bytes) -> "Comment":
    shared_access = SharedPostAccess.objects.get(post=post, user=author)
    author_key_obj = UserEncryptionKey.objects.get(user=author)
    author_private_key = author_key_obj.retrieve_private_key(master_key)
    post_key = unwrap_key_from_ecdh(
        bytes(shared_access.wrapped_key),
        bytes(shared_access.key_nonce),
        bytes(shared_access.ephemeral_public_key),
        author_private_key,
    )
    body_enc, body_nonce = encrypt_content(body.encode(), post_key)
    body_b64 = base64.b64encode(body_enc).decode()
    comment = Comment.objects.create(
        body=body_b64,
        body_nonce=body_nonce,
        author=author,
        bulletin_post=post,
    )
    return comment
```

**C) Implement `Comment.encrypt()` and `Comment.decrypt()` properly**

Actually — given that `CommentManager.create_classified()` handles encryption on creation and decryption can be a serializer concern, the `encrypt()`/`decrypt()` instance methods can be completed as thin wrappers or removed. The plan is to make them accept a `post_key: bytes` argument:

```python
def encrypt(self, post_key: bytes) -> None:
    ciphertext, nonce = encrypt_content(self.body.encode(), post_key)
    self.body = base64.b64encode(ciphertext).decode()
    self.body_nonce = nonce

def decrypt(self, post_key: bytes) -> str:
    ciphertext = base64.b64decode(self.body)
    return decrypt_content(ciphertext, post_key, bytes(self.body_nonce)).decode()
```

> Note: these aren't called by `create_classified` directly — they're utility methods for the serializer layer.

Also add imports to `bulletin/models.py`: `base64`, `wrap_key_for_recipient`, `unwrap_key_from_ecdh`, `UserEncryptionKey`, `encrypt_content`.

---

#### 3. `bulletin/serializers.py` — Implement all serializers

**`BulletinSerializer`** — read-only list/retrieve only for now:

```python
class BulletinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bulletin
        fields = ["id", "title", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
```

**`BulletinPostSerializer`** — handles classified and unclassified posts. For classified posts, accepts `password` in the write payload to derive `master_key` server-side, then calls `BulletinPost.objects.create_classified(...)`:

```python
class BulletinPostSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = BulletinPost
        fields = ["id", "title", "body", "is_classified", "bulletin",
                  "author", "created_at", "updated_at", "password"]
        read_only_fields = ["id", "author", "title_nonce", "body_nonce",
                            "created_at", "updated_at"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = self.context["request"].user
        is_classified = validated_data.get("is_classified", False)
        if is_classified:
            if not password:
                raise serializers.ValidationError("Password required for classified posts.")
            master_key = _derive_master_key(user, password)
            post = BulletinPost.objects.create_classified(
                title=validated_data["title"],
                body=validated_data["body"],
                author=user,
                bulletin=validated_data["bulletin"],
                master_key=master_key,
            )
            post.save()  # NOTE: fixing the missing save() here
            return post
        validated_data["author"] = user
        return BulletinPost.objects.create(**validated_data)

    def to_representation(self, instance):
        # Omit nonce fields from API response
        ...
```

**`SharePostAccessSerializer`** — accepts `recipient_username` + `password`:

```python
class SharePostAccessSerializer(serializers.Serializer):
    recipient_username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context["request"]
        post = self.context["post"]
        if post.author != request.user:
            raise serializers.ValidationError("Only the post author can share access.")
        try:
            attrs["recipient"] = User.objects.get(username=attrs["recipient_username"])
        except User.DoesNotExist:
            raise serializers.ValidationError("Recipient user not found.")
        if SharedPostAccess.objects.filter(post=post, user=attrs["recipient"]).exists():
            raise serializers.ValidationError("Access already granted.")
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        post = self.context["post"]
        master_key = _derive_master_key(request.user, validated_data["password"])
        return SharedPostAccess.create_for_user(
            post=post,
            recipient=validated_data["recipient"],
            grantor_master_key=master_key,
        )
```

**`CommentSerializer`** — for creating classified comments:

```python
class CommentSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Comment
        fields = ["id", "body", "bulletin_post", "author", "created_at",
                  "updated_at", "password"]
        read_only_fields = ["id", "author", "body_nonce", "created_at", "updated_at"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = self.context["request"].user
        post = validated_data["bulletin_post"]
        if post.is_classified:
            if not password:
                raise serializers.ValidationError("Password required to comment on classified posts.")
            master_key = _derive_master_key(user, password)
            return Comment.objects.create_classified(
                body=validated_data["body"],
                author=user,
                post=post,
                master_key=master_key,
            )
        validated_data["author"] = user
        return Comment.objects.create(**validated_data)
```

**Helper in `serializers.py`** (private, not a class):

```python
def _derive_master_key(user: User, password: str) -> bytes:
    key_obj = UserEncryptionKey.objects.get(user=user)
    password_key = derive_key(password, bytes(key_obj.key_salt))
    return key_obj._retrieve_key(password_key)
```

---

#### 4. `bulletin/views.py` — Implement views

All views use `knox.auth.TokenAuthentication` + `IsAuthenticated` (consistent with project-wide DRF default auth, but set explicitly to match `system/views.py` pattern):

```
BulletinListView        GET /api/bulletins/                    — list all bulletins
BulletinDetailView      GET /api/bulletins/<pk>/               — retrieve a bulletin
BulletinPostListView    GET /api/bulletins/<pk>/posts/         — list posts in a bulletin
                        POST /api/bulletins/<pk>/posts/        — create a post
BulletinPostDetailView  GET /api/bulletins/<pk>/posts/<post_pk>/   — retrieve a post
SharePostAccessView     POST /api/bulletins/<pk>/posts/<post_pk>/share/  — grant access
CommentListView         GET /api/bulletins/<pk>/posts/<post_pk>/comments/  — list comments
                        POST /api/bulletins/<pk>/posts/<post_pk>/comments/ — add a comment
```

---

#### 5. `bulletin/urls.py` — Wire up URL patterns

```python
urlpatterns = [
    path("", BulletinListView.as_view(), name="bulletin-list"),
    path("<int:pk>/", BulletinDetailView.as_view(), name="bulletin-detail"),
    path("<int:pk>/posts/", BulletinPostListView.as_view(), name="bulletinpost-list"),
    path("<int:pk>/posts/<int:post_pk>/", BulletinPostDetailView.as_view(), name="bulletinpost-detail"),
    path("<int:pk>/posts/<int:post_pk>/share/", SharePostAccessView.as_view(), name="share-post-access"),
    path("<int:pk>/posts/<int:post_pk>/comments/", CommentListView.as_view(), name="comment-list"),
]
```

---

#### 6. `bulletin/admin.py` — Register all models

```python
admin.site.register(Bulletin)
admin.site.register(BulletinPost)
admin.site.register(Comment)
admin.site.register(PostEncryptionKey)
admin.site.register(SharedPostAccess)
```

---

#### 7. New migration

A new migration is needed for `SharedPostAccess.ephemeral_public_key`. Run `python manage.py makemigrations bulletin`.

---

### What's explicitly NOT in scope

- Decryption at the read/list endpoint (decrypted content on GET) — the model layer has the tools, but exposing raw ciphertext vs. decrypting on-the-fly is a separate decision
- The missing `post.save()` bug in `BulletinPostManager.create_classified` — per your instruction, left alone; instead the serializer calls `post.save()` after `create_classified()`
- Tests

---

### One flag worth noting

The `system/views.py` views use `SessionAuthentication` while the project-wide DRF default is `knox.auth.TokenAuthentication`. The bulletin views should use Knox tokens (consistent with the rest of the API). I'll explicitly declare `authentication_classes = [TokenAuthentication]` on bulletin views rather than relying on the global default, matching the explicit style of `system/views.py`.
