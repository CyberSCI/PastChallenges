import pytest
from django.contrib.auth.models import User
from faker import Faker

from authentication.models import UserEncryptionKey
from bulletin.models import Bulletin, BulletinPost, Comment, SharedPostAccess


@pytest.fixture(name="bulletin")
def fixture_bulletin(db, faker: Faker):
    bulletin = Bulletin.objects.create(title=faker.catch_phrase())
    return bulletin


@pytest.fixture(name="post_title")
def fixture_bulletin_post_title(faker: Faker):
    return " ".join(faker.words(5))


@pytest.fixture(name="post_body")
def fixture_bulletin_post_body(faker: Faker):
    return "\n\n".join(faker.paragraphs(3))


@pytest.fixture(name="bulletin_post")
def fixture_bulletin_post(
    bulletin: Bulletin, author_obj: User, post_title: str, post_body: str
):
    post = BulletinPost.objects.create(
        bulletin=bulletin, author=author_obj, title=post_title, body=post_body
    )
    return post


@pytest.fixture(name="classified_bulletin_post")
def fixture_classified_bulletin_post(
    bulletin: Bulletin,
    author: User,
    author_obj: User,
    post_title: str,
    post_body: str,
):
    title = post_title
    body = post_body
    user_key = UserEncryptionKey.objects.get(user=author_obj)
    user_key_value = user_key.get_user_key(author.password)
    post: BulletinPost = BulletinPost.objects.create_classified(  # type: ignore
        title, body, author_obj, bulletin, user_key_value
    )
    return post


@pytest.fixture(name="comment_body")
def fixture_comment_body(faker: Faker):
    return "\n\n".join(faker.paragraphs(2))


@pytest.fixture(name="comment")
def fixture_comment(
    bulletin_post: BulletinPost, author_obj: User, comment_body: str
):
    comment = Comment.objects.create(
        bulletin_post=bulletin_post, author=author_obj, body=comment_body
    )
    return comment


@pytest.fixture(name="classified_comment")
def fixture_classified_comment(
    author: User,
    classified_bulletin_post: BulletinPost,
    comment_body: str,
    user: User,
    user_obj: User,
):
    commenter = user
    commenter_obj = user_obj
    author_key_obj = UserEncryptionKey.objects.get(
        user=classified_bulletin_post.author
    )
    author_key = author_key_obj.get_user_key(author.password)
    commenter_key_obj = UserEncryptionKey.objects.get(user=commenter_obj)
    commenter_key = commenter_key_obj.get_user_key(commenter.password)
    shared_post_key = SharedPostAccess.create_for_user(
        post=classified_bulletin_post,
        recipient=commenter_obj,
        sender=classified_bulletin_post.author,
        sender_user_key=author_key,
    )

    commenter_private_key = commenter_key_obj.retrieve_private_key(
        commenter_key
    )
    post_key = shared_post_key.unwrap(
        author_key_obj.public_key,
        commenter_private_key,
    )

    body_enc, body_nonce = shared_post_key.encrypt(comment_body, post_key)
    comment = Comment.objects.create(
        author=commenter_obj,
        body=body_enc,
        body_nonce=body_nonce,
        bulletin_post=classified_bulletin_post,
    )
    return comment
