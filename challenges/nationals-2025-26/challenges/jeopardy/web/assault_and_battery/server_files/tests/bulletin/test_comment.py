from collections.abc import Callable

from django.contrib.auth.models import User

from bulletin.models import BulletinPost, Comment


def test_comment(
    db,
    bulletin_post: BulletinPost,
    user_obj: User,
    comment_body: str,
):
    author = user_obj
    body = comment_body
    comment = Comment.objects.create(
        author=author, body=body, bulletin_post=bulletin_post
    )
    assert comment.body == body
    assert comment.pk != 0
    assert comment.author == author


def test_classified_comment(
    classified_comment: Comment,
    comment_body: str,
    user_obj: User,
):
    commenter_obj = user_obj
    assert classified_comment.body != comment_body
    assert classified_comment.pk != 0
    assert classified_comment.author == commenter_obj


def test_classified_comment_decrypt(
    classified_comment: Comment,
    comment_body: str,
    user: User,
    user_obj: User,
):
    decrypted_comment = classified_comment.decrypted(user_obj, user.password)
    assert decrypted_comment is not None
    assert decrypted_comment.body == comment_body


def test_unauthorized_comment_access(
    classified_comment: Comment,
    create_user: Callable[[], User],
):
    user = create_user()
    user_obj = User.objects.get(username=user.username)
    decrypted_comment = classified_comment.decrypted(user_obj, user.password)
    assert decrypted_comment is None


def test_failed_comment_decrypt(
    classified_comment: Comment,
    user_obj: User,
):
    decrypted_comment = classified_comment.decrypted(user_obj, "wrongpassword")
    assert decrypted_comment is None
