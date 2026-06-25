# Step 3: TestComments Implementation

**File:** `tests/bulletin/test_views.py`

Replace `TestComments` class:

```python
class TestComments:
    def test_create_comment(
        self,
        login_client: Client,
        bulletin_post: BulletinPost,
        comment_body: str,
    ):
        response = _api_create_comment(login_client, bulletin_post, comment_body)
        assert response.status_code == 201
        assert response.json()["body"] == comment_body

    def test_list_comments_from_post(
        self,
        login_client: Client,
        bulletin_post: BulletinPost,
        comment_body: str,
    ):
        _api_create_comment(login_client, bulletin_post, comment_body)
        list_response = login_client.get(
            f"/api/bulletins/posts/{bulletin_post.pk}/comments/"
        )
        assert list_response.status_code == 200
        comments = list_response.json()
        assert len(comments) == 1
        assert comments[0]["body"] == comment_body

    def test_get_comment(
        self,
        login_client: Client,
        bulletin_post: BulletinPost,
        comment_body: str,
    ):
        create_response = _api_create_comment(login_client, bulletin_post, comment_body)
        comment_id = create_response.json()["id"]
        get_response = login_client.get(f"/api/bulletins/comments/{comment_id}/")
        assert get_response.status_code == 200
        assert get_response.json()["body"] == comment_body
```
