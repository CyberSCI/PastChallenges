from django.db.models import Q, QuerySet

from forum.models import Comment, Post, User


def is_admin(user):
    return bool(
        user
        and user.is_authenticated
        and user.is_active
        and user.approval_status == User.ApprovalStatus.APPROVED
        and user.is_staff
    )


def visible_posts(user) -> QuerySet[Post]:
    posts = Post.objects.select_related("author")
    if is_admin(user):
        return posts
    if user and user.is_authenticated:
        return posts.filter(Q(visibility=Post.Visibility.PUBLIC) | Q(visibility=Post.Visibility.AUTHENTICATED))
    return posts.filter(visibility=Post.Visibility.PUBLIC)


def visible_comments(post: Post, user) -> QuerySet[Comment]:
    comments = post.comments.select_related("author")
    if is_admin(user):
        return comments
    return comments.filter(is_hidden=False)


def can_access_post(post: Post, user) -> bool:
    if is_admin(user):
        return True
    if post.visibility == Post.Visibility.PUBLIC:
        return True
    return bool(user and user.is_authenticated and post.visibility == Post.Visibility.AUTHENTICATED)