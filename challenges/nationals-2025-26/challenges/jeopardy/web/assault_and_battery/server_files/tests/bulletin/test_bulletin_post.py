import pytest
from django.contrib.auth.models import User

from authentication.models import UserEncryptionKey
from bulletin.models import Bulletin, BulletinPost, SharedPostAccess


def test_bulletin_post(
    db,
    bulletin: Bulletin,
    user_obj: User,
    post_title: str,
    post_body: str,
):
    author = user_obj
    title = post_title
    body = post_body
    post = BulletinPost.objects.create(
        title=title, body=body, author=author, bulletin=bulletin
    )
    assert post.title == title
    assert post.body == body
    assert post.pk != 0
    assert post.author == author


def test_classified_bulletin_post(
    db,
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
    post: BulletinPost = BulletinPost.objects.create_classified(
        title, body, author_obj, bulletin, user_key_value
    )

    assert post.title != title
    assert post.title_nonce is not None
    assert post.body != body
    assert post.body_nonce is not None
    assert post.pk != 0
    assert post.author == author_obj


def test_classified_bulletin_post_decrypt(
    db,
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

    decrypted_title = post.decrypt_title(author.password)
    decrypted_body = post.decrypt_body(author.password)

    assert decrypted_title == title
    assert decrypted_body == body


def test_classified_bulletin_post_failed_decrypt(
    db,
    bulletin: Bulletin,
    author: User,
    author_obj: User,
    commenter: User,
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
    with pytest.raises(ValueError):
        decrypted_title = post.decrypt_title(commenter.password)
        assert decrypted_title == title
    with pytest.raises(ValueError):
        decrypted_body = post.decrypt_body(commenter.password)
        assert decrypted_body == body


def test_post_sharing(
    db,
    bulletin: Bulletin,
    author: User,
    author_obj: User,
    commenter: User,
    commenter_obj: User,
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

    _ = SharedPostAccess.create_for_user(
        post, commenter_obj, author_obj, user_key_value
    )

    decrypted_title = post.decrypt_title_as(commenter_obj, commenter.password)
    decrypted_body = post.decrypt_body_as(commenter_obj, commenter.password)
    assert decrypted_title == title
    assert decrypted_body == body
