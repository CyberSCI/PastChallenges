# Step 4: TestClassifiedComments Implementation

**File:** `tests/bulletin/test_views.py`

Replace `TestClassifiedComments` class.

**Key flow:** Author creates classified post → shares with commenter → commenter can create encrypted comment and decrypt it.

```python
class TestClassifiedComments:
    def test_create_comment(
        self,
        login_client_for: Callable[[User], Client],
        classified_post: BulletinPost,
        author: User,
        create_user: Callable[[], User],
        comment_body: str,
    ):
        commenter = create_user()
        # Share post with commenter first
        author_client = login_client_for(author)
        _api_share_post(author_client, commenter, author, classified_post)

        commenter_client = login_client_for(commenter)
        response = _api_create_comment(
            commenter_client, classified_post, comment_body, password=commenter.password
        )
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["body"] != comment_body
        assert response_data["body_nonce"]

    def test_list_comments_from_post(
        self,
        login_client_for: Callable[[User], Client],
        classified_post: BulletinPost,
        author: User,
        create_user: Callable[[], User],
        bulletin: Bulletin,
        comment_body: str,
    ):
        commenter = create_user()
        author_client = login_client_for(author)
        _api_share_post(author_client, commenter, author, classified_post)

        commenter_client = login_client_for(commenter)
        _api_create_comment(
            commenter_client, classified_post, comment_body, password=commenter.password
        )

        list_response = commenter_client.get(
            f"/api/bulletins/posts/{classified_post.pk}/comments/"
        )
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1

    def test_get_comment(
        self,
        login_client_for: Callable[[User], Client],
        classified_post: BulletinPost,
        author: User,
        create_user: Callable[[], User],
        comment_body: str,
    ):
        commenter = create_user()
        author_client = login_client_for(author)
        _api_share_post(author_client, commenter, author, classified_post)

        commenter_client = login_client_for(commenter)
        create_response = _api_create_comment(
            commenter_client, classified_post, comment_body, password=commenter.password
        )
        comment_id = create_response.json()["id"]

        get_response = commenter_client.get(f"/api/bulletins/comments/{comment_id}/")
        assert get_response.status_code == 200

    def test_decrypt_comment(
        self,
        login_client_for: Callable[[User], Client],
        classified_post: BulletinPost,
        author: User,
        create_user: Callable[[], User],
        comment_body: str,
    ):
        commenter = create_user()
        author_client = login_client_for(author)
        _api_share_post(author_client, commenter, author, classified_post)

        commenter_client = login_client_for(commenter)
        create_response = _api_create_comment(
            commenter_client, classified_post, comment_body, password=commenter.password
        )
        comment_id = create_response.json()["id"]

        decrypt_response = commenter_client.post(
            f"/api/bulletins/comments/{comment_id}/decrypted/",
            data={"password": commenter.password},
        )
        assert decrypt_response.status_code == 200
        assert decrypt_response.json()["body"] == comment_body
```

**Note:** `Comment` import already exists at top of file. `Callable` and `User` imports also present.
