# Step 2: Test Fixtures & Helpers

## 2a. Add `comment_body` fixture

**File:** `tests/bulletin/conftest.py`

```python
@pytest.fixture(name="comment_body")
def fixture_comment_body(faker: Faker):
    return "\n\n".join(faker.paragraphs(2))
```

## 2b. Add `_api_create_comment` helper

**File:** `tests/bulletin/test_views.py`

Add after `_api_share_post`:
```python
def _api_create_comment(
    client: Client,
    bulletin_post: BulletinPost,
    body: str,
    password: str | None = None,
):
    data: dict[str, str | int] = {"body": body, "bulletin_post": bulletin_post.pk}
    if password:
        data["password"] = password
    return client.post(
        f"/api/bulletins/posts/{bulletin_post.pk}/comments/",
        data=data,
    )
```
