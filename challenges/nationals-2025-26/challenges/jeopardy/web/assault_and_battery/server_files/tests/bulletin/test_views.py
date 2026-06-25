from collections.abc import Callable

import pytest
from django.contrib.auth.models import User
from django.test import Client

from bulletin.models import Bulletin, BulletinPost, Comment


@pytest.fixture(name="login_client_for")
def fixture_login_client_for(db, client: Client):
    def _create_client(target_user: User):
        login_data = {
            "username": target_user.username,
            "password": target_user.password,
        }
        login_response = client.post(
            "/api/auth/login/",
            data=login_data,
        )

        assert login_response.status_code == 200

        return client

    return _create_client


@pytest.fixture(name="login_client")
def fixture_login_client(
    db, login_client_for: Callable[[User], Client], user: User
):
    yield login_client_for(user)


@pytest.fixture(name="admin_client")
def fixture_admin_client(
    db, login_client_for: Callable[[User], Client], admin_user: User
):
    yield login_client_for(admin_user)


def _api_create_post(
    client: Client,
    bulletin: Bulletin,
    title: str,
    body: str,
    is_classified: bool = False,
    password: str | None = None,
):
    data = {
        "title": title,
        "body": body,
        "is_classified": is_classified,
        "bulletin": bulletin.pk,
    }
    if is_classified:
        data.update({"password": password})

    bulletin_post_response = client.post(
        f"/api/bulletins/{bulletin.pk}/posts/", data=data
    )
    return bulletin_post_response


def _api_share_post(
    client: Client, recipient: User, author: User, bulletin_post: BulletinPost
):
    data = {
        "recipient_username": recipient.username,
        "password": author.password,
    }
    share_response = client.post(
        f"/api/bulletins/posts/{bulletin_post.pk}/share/", data=data
    )
    return share_response


def _api_create_comment(
    client: Client,
    bulletin_post: BulletinPost,
    body: str,
    password: str | None = None,
):
    data: dict[str, str | int] = {
        "body": body,
        "bulletin_post": bulletin_post.pk,
    }
    if password:
        data["password"] = password
    return client.post(
        f"/api/bulletins/posts/{bulletin_post.pk}/comments/",
        data=data,
    )


class TestBulletin:
    def test_create_bulletin(self, admin_client: Client):
        title = "General"

        data = {"title": title}
        bulletin_response = admin_client.post("/api/bulletins/", data=data)

        assert bulletin_response.status_code == 201
        assert bulletin_response.json()["title"] == title

    def test_list_bulletins(
        self,
        login_client: Client,
        bulletin: Bulletin,
    ):
        bulletin_response = login_client.get("/api/bulletins/")

        assert bulletin_response.status_code == 200
        assert bulletin_response.json()[0]["title"] == bulletin.title

    def test_get_bulletin(self, login_client: Client, bulletin: Bulletin):
        bulletin_response = login_client.get(f"/api/bulletins/{bulletin.pk}/")

        assert bulletin_response.status_code == 200
        assert bulletin_response.json()["title"] == bulletin.title

    def test_unauthenticated_create_bulletin(
        self, client: Client, bulletin: Bulletin
    ):
        title = "General"

        data = {"title": title}
        bulletin_response = client.post("/api/bulletins/", data=data)

        assert bulletin_response.status_code == 403
        assert (
            bulletin_response.json()["detail"]
            == "Authentication credentials were not provided."
        )


class TestBulletinPost:
    def test_create_post(
        self,
        login_client: Client,
        bulletin: Bulletin,
        post_title: str,
        post_body: str,
    ):
        bulletin_post_response = _api_create_post(
            login_client, bulletin, title=post_title, body=post_body
        )
        assert bulletin_post_response.status_code == 201
        response_data = bulletin_post_response.json()
        assert response_data["title"] == post_title
        assert response_data["body"] == post_body

    def test_list_posts_from_bulletin(
        self,
        login_client: Client,
        bulletin: Bulletin,
        bulletin_post: BulletinPost,
        post_title: str,
    ):

        post_list_response = login_client.get(
            f"/api/bulletins/{bulletin.pk}/posts/"
        )
        assert post_list_response.status_code == 200
        post_list_response_data = post_list_response.json()
        first_post = post_list_response_data[0]
        assert first_post["title"] == post_title
        assert first_post["title"] == bulletin_post.title

    def test_get_bulletin_post(
        self,
        login_client: Client,
        bulletin_post: BulletinPost,
    ):
        bulletin_post_response = login_client.get(
            f"/api/bulletins/posts/{bulletin_post.pk}/"
        )
        assert bulletin_post_response.status_code == 200

    def test_share_post(
        self,
        login_client_for: Callable[[User], Client],
        author: User,
        create_user: Callable[[], User],
        bulletin_post: BulletinPost,
    ):
        login_client = login_client_for(author)
        recipient = create_user()
        share_response = _api_share_post(
            login_client, recipient, author, bulletin_post
        )
        assert share_response.status_code == 400


class TestClassifiedBulletinPost:
    def test_create_post(
        self,
        login_client_for: Callable[[User], Client],
        author: User,
        bulletin: Bulletin,
        post_title: str,
        post_body: str,
    ):
        login_client = login_client_for(author)
        bulletin_post_response = _api_create_post(
            login_client,
            bulletin,
            post_title,
            post_body,
            is_classified=True,
            password=author.password,
        )

        assert bulletin_post_response.status_code == 201
        response_data = bulletin_post_response.json()
        assert response_data["title"] != post_title
        assert response_data["title_nonce"]
        assert response_data["body"] != post_body
        assert response_data["body_nonce"]

    def test_list_classified_posts(
        self,
        bulletin: Bulletin,
        classified_bulletin_post: BulletinPost,
        login_client_for: Callable[[User], Client],
        author: User,
    ):
        login_client = login_client_for(author)
        post_list_response = login_client.get(
            f"/api/bulletins/{bulletin.pk}/posts/"
        )
        assert post_list_response.status_code == 200
        post_list_response_data = post_list_response.json()
        first_post = post_list_response_data[0]
        assert first_post["id"] == classified_bulletin_post.pk

    def test_get_classified_post(
        self,
        bulletin: Bulletin,
        classified_bulletin_post: BulletinPost,
        login_client_for: Callable[[User], Client],
        author: User,
    ):
        login_client = login_client_for(author)
        post_response = login_client.get(
            f"/api/bulletins/posts/{classified_bulletin_post.pk}/"
        )
        assert post_response.status_code == 200
        response_data = post_response.json()
        assert response_data["id"] == classified_bulletin_post.pk
        assert response_data["bulletin"] == bulletin.pk

    def test_decrypt_classified_post(
        self,
        classified_bulletin_post: BulletinPost,
        login_client_for: Callable[[User], Client],
        author: User,
        post_title: str,
        post_body: str,
    ):
        login_client = login_client_for(author)
        post_response = login_client.post(
            f"/api/bulletins/posts/{classified_bulletin_post.pk}/decrypted/",
            data={"password": author.password},
        )
        assert post_response.status_code == 200
        response_data = post_response.json()
        assert response_data["title"] == post_title
        assert response_data["body"] == post_body

    def test_share(
        self,
        classified_bulletin_post: BulletinPost,
        login_client_for: Callable[[User], Client],
        author: User,
        create_user: Callable[[], User],
        post_title: str,
        post_body: str,
    ):
        recipient = create_user()
        author_client = login_client_for(author)

        share_response = _api_share_post(
            author_client, recipient, author, classified_bulletin_post
        )

        assert share_response.status_code == 204

        recipient_client = login_client_for(recipient)

        post_response = recipient_client.post(
            f"/api/bulletins/posts/{classified_bulletin_post.pk}/decrypted/",
            data={"password": recipient.password},
        )

        assert post_response.status_code == 200
        response_data = post_response.json()
        assert response_data["title"] == post_title
        assert response_data["body"] == post_body


class TestComments:
    def test_create_comment(
        self,
        login_client: Client,
        bulletin_post: BulletinPost,
        comment_body: str,
    ):
        response = _api_create_comment(
            login_client, bulletin_post, comment_body
        )
        assert response.status_code == 201
        assert response.json()["body"] == comment_body

    def test_list_comments_from_post(
        self,
        login_client: Client,
        bulletin_post: BulletinPost,
        comment: Comment,
    ):
        list_response = login_client.get(
            f"/api/bulletins/posts/{bulletin_post.pk}/comments/"
        )
        assert list_response.status_code == 200
        comments = list_response.json()
        assert len(comments) == 1
        assert comments[0]["body"] == comment.body

    def test_get_comment(
        self,
        login_client: Client,
        comment: Comment,
    ):
        get_response = login_client.get(
            f"/api/bulletins/comments/{comment.pk}/"
        )
        assert get_response.status_code == 200
        assert get_response.json()["body"] == comment.body


class TestClassifiedComments:
    def test_create_comment(
        self,
        login_client_for: Callable[[User], Client],
        classified_bulletin_post: BulletinPost,
        author: User,
        create_user: Callable[[], User],
        comment_body: str,
    ):
        commenter = create_user()
        # Share post with commenter first
        author_client = login_client_for(author)
        _ = _api_share_post(
            author_client, commenter, author, classified_bulletin_post
        )

        commenter_client = login_client_for(commenter)
        response = _api_create_comment(
            commenter_client,
            classified_bulletin_post,
            comment_body,
            password=commenter.password,
        )
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["body"] != comment_body
        assert response_data["body_nonce"]

    def test_list_comments_from_post(
        self,
        classified_bulletin_post: BulletinPost,
        classified_comment: Comment,
        login_client: Client,
    ):
        list_response = login_client.get(
            f"/api/bulletins/posts/{classified_bulletin_post.pk}/comments/"
        )
        assert list_response.status_code == 200
        comments = list_response.json()
        assert len(comments) == 1
        assert comments[0]["body"] == classified_comment.body

    def test_get_comment(
        self, classified_comment: Comment, login_client: Client
    ):
        get_response = login_client.get(
            f"/api/bulletins/comments/{classified_comment.pk}/"
        )
        assert get_response.status_code == 200
        assert get_response.json()["body"] == classified_comment.body

    def test_decrypt(
        self,
        classified_comment: Comment,
        login_client: Client,
        user: User,
        comment_body: str,
    ):
        get_response = login_client.post(
            f"/api/bulletins/comments/{classified_comment.pk}/decrypted/",
            data={"password": user.password},
        )
        assert get_response.status_code == 200
        assert get_response.json()["body"] == comment_body
