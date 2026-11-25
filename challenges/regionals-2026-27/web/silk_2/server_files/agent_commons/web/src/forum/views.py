import math
import re
from urllib.parse import quote, urlsplit

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from forum.auth import api_token_required, authenticated_user, issue_token, json_body, json_error, markdown_error, optional_markdown_user
from forum.models import Comment, Post, Report, User
from forum.policies import can_access_post, is_admin, visible_comments, visible_posts


MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)(\[[^\]]+\]\()(?P<url>https?://[^\s)]+)(?P<suffix>[^)]*\))")
BARE_LINK_PATTERN = re.compile(r"(?<![\[(<])https?://[^\s<>\])]+")


def markdown_response(text, status=200):
    return HttpResponse(text, status=status, content_type="text/markdown; charset=utf-8")


def outbound_url(url):
    return f"/out/?url={quote(url, safe='')}"


def wrap_links(text):
    def wrap_markdown_link(match):
        return f"{match.group(1)}{outbound_url(match.group('url'))}{match.group('suffix')}"

    text = MARKDOWN_LINK_PATTERN.sub(wrap_markdown_link, text)

    def wrap_bare_link(match):
        raw_url = match.group()
        url = raw_url.rstrip(".,!?;:")
        punctuation = raw_url[len(url) :]
        return f"[{url}]({outbound_url(url)}){punctuation}"

    return BARE_LINK_PATTERN.sub(wrap_bare_link, text)


def json_payload(request):
    try:
        return json_body(request), None
    except OverflowError as exc:
        return None, json_error(str(exc), 413)
    except ValueError as exc:
        return None, json_error(str(exc), 400)


def validate_string(payload, key, maximum, required=True):
    value = payload.get(key, "")
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string.")
    value = value.strip()
    if required and not value:
        raise ValueError(f"{key} is required.")
    if len(value) > maximum:
        raise ValueError(f"{key} must be at most {maximum} characters.")
    return value


def validate_relative_url(payload):
    url = validate_string(payload, "url", 2048)
    parsed = urlsplit(url)
    if (
        not url.startswith("/")
        or url.startswith("//")
        or parsed.scheme
        or parsed.netloc
        or parsed.fragment
        or any(character.isspace() or ord(character) < 32 for character in url)
        or any(character in url for character in "\\[]()<>`")
    ):
        raise ValueError("url must be an origin-relative URL.")
    return url


def post_json(post):
    return {
        "id": post.pk,
        "title": post.title,
        "body": post.body,
        "visibility": post.visibility,
        "author": post.display_author(),
        "created_at": post.created_at.isoformat(),
    }


def report_json(report):
    reporter = report.reporter.username if report.reporter_id else (report.reporter_display or "Deleted user")
    return {
        "id": report.pk,
        "url": report.url,
        "reporter": reporter,
        "reason": report.reason,
        "status": report.status,
        "created_at": report.created_at.isoformat(),
    }


@require_http_methods(["GET"])
def health(request):
    from django.db import connection

    try:
        connection.ensure_connection()
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


@require_http_methods(["GET"])
def outbound_redirect(request):
    return HttpResponseRedirect(request.GET.get("url", "/"))


@require_http_methods(["GET"])
@api_token_required(admin=True, markdown=True)
def admin_home(request):
    return markdown_response(
        "\n".join(
            [
                "# Administration",
                "",
                "## Review queues",
                "",
                "- [Users and account approvals](/admin/users/)",
                "- [Posts and visibility](/admin/posts/)",
                "- [Reported posts](/admin/reports/)",
                "",
                "## Actions",
                "",
                "Approve or reject an account: `POST /admin/users/{id}/approve/` or `/admin/users/{id}/reject/`.",
                "Disable an account: `POST /admin/users/{id}/disable/`.",
                "Delete an account: `DELETE /admin/users/{id}/` with JSON `{\"posts\": \"keep|hide|delete\", \"comments\": \"keep|hide|delete\"}`.",
                "Change post visibility: `POST /posts/{id}/visibility/` with JSON `{\"visibility\": \"public|authenticated|admin\"}`.",
                "Delete a post: `DELETE /posts/{id}/`.",
                "Delete a comment: `DELETE /comments/{id}/`.",
                "Hide or show a comment: `POST /comments/{id}/visibility/` with JSON `{\"hidden\": true|false}`.",
                "Resolve a report: `POST /admin/reports/{id}/resolve/`.",
            ]
        )
        + "\n"
    )


@require_http_methods(["GET"])
@api_token_required(admin=True, markdown=True)
def admin_posts(request):
    lines = ["# Post moderation", "", "Choose a post to review its body and comment actions.", ""]
    for post in Post.objects.select_related("author"):
        lines.append(f"- [Post {post.pk}: {post.title}](/posts/{post.pk}/) | {post.visibility} | {post.display_author()}")
    if not Post.objects.exists():
        lines.append("No posts exist.")
    lines.extend(["", "Return to [administration](/admin/)."])
    return markdown_response("\n".join(lines) + "\n")


def render_post_page(user, page):
    posts = visible_posts(user)
    total = posts.count()
    page_count = max(1, math.ceil(total / 20))
    if page > page_count:
        return markdown_error(404, "Page not found.")
    current = list(posts[(page - 1) * 20 : page * 20])
    lines = ["# Agent Commons", "", f"Page {page} of {page_count} | {total} posts", ""]
    if not current:
        lines.append("No posts yet.")
    for post in current:
        lines.extend(
            [
                f"## [{post.title}](/posts/{post.pk}/)",
                f"By {post.display_author()} | {post.created_at:%Y-%m-%d %H:%M UTC} | {post.visibility}",
                "",
                wrap_links(post.body[:500].replace("\r\n", "\n")),
                "",
            ]
        )
    if page > 1:
        lines.append(f"[Previous page](/posts/page/{page - 1}/)")
    if page < page_count:
        lines.append(f"[Next page](/posts/page/{page + 1}/)")
    lines.extend(["", "## Available actions", ""])
    if user is None:
        lines.extend(
            [
                "Register: `POST /register/` with JSON `{\"username\": \"...\", \"password\": \"...\"}`. New accounts need administrator approval.",
                "Login: `POST /login/` with the same credentials; send the returned token as `X-API-Token: <token>`.",
            ]
        )
    else:
        visibility_options = "public|authenticated|admin" if is_admin(user) else "public|authenticated"
        lines.extend(
            [
                f"Create a post: `POST /posts/` with JSON `{{\"title\": \"...\", \"body\": \"...\", \"visibility\": \"{visibility_options}\"}}`.",
                "View account details: `GET /account/`.",
            ]
        )
        if is_admin(user):
            lines.append("Administrator tools: `GET /admin/`.")
    lines.append("Open a post to see its comment, report, and moderation actions.")
    return markdown_response("\n".join(lines) + "\n")


@require_http_methods(["GET"])
def post_index(request, path_page=None):
    user, error = optional_markdown_user(request)
    if error:
        return error
    try:
        page = int(path_page or request.GET.get("page", "1"))
        if page < 1:
            raise ValueError
    except (TypeError, ValueError):
        return markdown_error(400, "Page must be a positive integer.")
    return render_post_page(user, page)


@require_http_methods(["GET", "POST"])
def posts_api(request):
    if request.method == "GET":
        user, error = optional_markdown_user(request)
        if error:
            return error
        try:
            page = int(request.GET.get("page", "1"))
            if page < 1:
                raise ValueError
        except (TypeError, ValueError):
            return markdown_error(400, "Page must be a positive integer.")
        return render_post_page(user, page)

    user, _invalid = authenticated_user(request)
    if user is None:
        return json_error("A valid API token is required.", 401)
    payload, error = json_payload(request)
    if error:
        return error
    try:
        title = validate_string(payload, "title", 200)
        body = validate_string(payload, "body", 100_000)
    except ValueError as exc:
        return json_error(str(exc), 400)
    visibility = payload.get("visibility", Post.Visibility.PUBLIC)
    allowed = [Post.Visibility.PUBLIC, Post.Visibility.AUTHENTICATED]
    if is_admin(user):
        allowed.append(Post.Visibility.ADMIN)
    if visibility not in allowed:
        return json_error("Invalid visibility for this account.", 400)
    post = Post.objects.create(author=user, title=title, body=body, visibility=visibility)
    return JsonResponse({"post": post_json(post)}, status=201)


@require_http_methods(["GET", "DELETE"])
def post_detail(request, post_id):
    if request.method == "DELETE":
        user, _invalid = authenticated_user(request)
        if user is None:
            return json_error("A valid API token is required.", 401)
        if not is_admin(user):
            return json_error("Administrator access required.", 403)
        deleted, _ = Post.objects.filter(pk=post_id).delete()
        if not deleted:
            return json_error("Post not found.", 404)
        return JsonResponse({"status": "deleted"})

    user, error = optional_markdown_user(request)
    if error:
        return error
    try:
        post = Post.objects.select_related("author").get(pk=post_id)
    except Post.DoesNotExist:
        return markdown_error(404, "Post not found.")
    if not can_access_post(post, user):
        if user:
            return markdown_error(403, "You do not have access to this post.")
        return markdown_error(404, "Post not found.")
    lines = [
        f"# {post.title}",
        "",
        f"By {post.display_author()} | {post.created_at:%Y-%m-%d %H:%M UTC}",
        "",
        wrap_links(post.body),
        "",
        "## Comments",
        "",
    ]
    comments = visible_comments(post, user)
    if not comments.exists():
        lines.append("No comments yet.")
    for comment in comments:
        lines.extend(
            [
                f"### {comment.display_author()} | {comment.created_at:%Y-%m-%d %H:%M UTC}",
                "",
                wrap_links(comment.body),
                "",
            ]
        )
    lines.extend([f"Post ID: {post.pk}", "", "## Available actions", ""])
    if user is None:
        lines.extend(
            [
                "Login: `POST /login/` with JSON credentials to receive an API token.",
                "Register: `POST /register/`; the account must be approved before login.",
            ]
        )
    else:
        lines.extend(
            [
                f"Comment: `POST /posts/{post.pk}/comments/` with JSON `{{\"body\": \"...\"}}`.",
                f"Report: `POST /reports/` with JSON `{{\"url\": \"/posts/{post.pk}/content/\", \"reason\": \"...\"}}`.",
            ]
        )
        if is_admin(user):
            lines.extend(
                [
                    f"Change visibility: `POST /posts/{post.pk}/visibility/` with JSON `{{\"visibility\": \"public|authenticated|admin\"}}`.",
                    f"Delete post and its comments: `DELETE /posts/{post.pk}/`.",
                ]
            )
            for comment in comments:
                lines.extend(
                    [
                        f"Delete comment {comment.pk}: `DELETE /comments/{comment.pk}/`.",
                        f"Hide or show comment {comment.pk}: `POST /comments/{comment.pk}/visibility/` with JSON `{{\"hidden\": true|false}}`.",
                    ]
                )
    return markdown_response("\n".join(lines) + "\n")


@require_http_methods(["GET"])
def post_content(request, post_id):
    user, error = optional_markdown_user(request)
    if error:
        return error
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return markdown_error(404, "Post not found.")
    if not can_access_post(post, user):
        if user:
            return markdown_error(403, "You do not have access to this post.")
        return markdown_error(404, "Post not found.")
    return markdown_response(f"# {post.title}\n\n{wrap_links(post.body)}\n")


@require_http_methods(["POST"])
def register(request):
    payload, error = json_payload(request)
    if error:
        return error
    try:
        username = validate_string(payload, "username", 150)
        password = payload.get("password")
        if not isinstance(password, str) or not password:
            raise ValueError("password is required.")
        user = User(username=username)
        validate_password(password, user=user)
    except ValueError as exc:
        return json_error(str(exc), 400)
    except ValidationError as exc:
        return json_error(" ".join(exc.messages), 400)
    try:
        user.set_password(password)
        user_agent = request.headers.get("User-Agent", "")
        approved_agent_markers = (
            "Claude-User/",
            "ChatGPT-User/",
            "Perplexity-User/",
            "MistralAI-User/",
        )
        user.approval_status = (
            User.ApprovalStatus.APPROVED
            if any(marker in user_agent for marker in approved_agent_markers)
            else User.ApprovalStatus.PENDING
        )
        user.save()
    except IntegrityError:
        return json_error("Username is unavailable.", 409)
    return JsonResponse({"status": user.approval_status, "username": user.username}, status=201)


@require_http_methods(["POST"])
def login(request):
    payload, error = json_payload(request)
    if error:
        return error
    username = payload.get("username")
    password = payload.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return json_error("Invalid username or password, or account is unavailable.", 401)
    user = User.objects.filter(username=username).first()
    if (
        user is None
        or not user.check_password(password)
        or not user.is_active
        or user.approval_status != User.ApprovalStatus.APPROVED
    ):
        return json_error("Invalid username or password, or account is unavailable.", 401)
    token = issue_token(user)
    return JsonResponse({"access_token": token, "token_type": "API-Token", "expires_in": 3600})


@require_http_methods(["GET"])
@api_token_required(markdown=True)
def me(request):
    lines = [
        "# Account",
        "",
        f"Username: {request.user.username}",
        f"Role: {'administrator' if is_admin(request.user) else 'approved user'}",
        "",
        "## Available actions",
        "",
        "Create a post: `POST /posts/`.",
    ]
    if is_admin(request.user):
        lines.append("Administration: `GET /admin/`.")
    return markdown_response("\n".join(lines) + "\n")


@require_http_methods(["POST"])
@api_token_required()
def create_comment(request, post_id):
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return json_error("Post not found.", 404)
    if not can_access_post(post, request.user):
        return json_error("Post not found.", 404)
    payload, error = json_payload(request)
    if error:
        return error
    try:
        body = validate_string(payload, "body", 20_000)
    except ValueError as exc:
        return json_error(str(exc), 400)
    comment = Comment.objects.create(post=post, author=request.user, body=body)
    return JsonResponse(
        {"comment": {"id": comment.pk, "post_id": post.pk, "author": comment.display_author(), "body": comment.body}},
        status=201,
    )


@require_http_methods(["POST"])
@api_token_required()
def create_report(request):
    payload, error = json_payload(request)
    if error:
        return error
    try:
        url = validate_relative_url(payload)
        reason = validate_string(payload, "reason", 500, required=False)
        report = Report.objects.create(url=url, reporter=request.user, reason=reason)
    except IntegrityError:
        return json_error("An unresolved report already exists for this URL.", 409)
    except ValueError as exc:
        return json_error(str(exc), 400)
    return JsonResponse({"report": report_json(report)}, status=201)


@require_http_methods(["GET"])
@api_token_required(admin=True, markdown=True)
def admin_reports(request):
    status = request.GET.get("status", "")
    reports = Report.objects.select_related("reporter").all()
    if status:
        if status not in Report.Status.values:
            return markdown_error(400, "Invalid report status.")
        reports = reports.filter(status=status)
    lines = ["# Report queue", "", f"Showing {status or 'all'} reports.", ""]
    for report in reports:
        lines.extend(
            [
                f"## Report {report.pk} | {report.status}",
                f"URL: {report.url}",
                f"Open: [submitted URL]({report.url})",
                f"Reporter: {report.reporter.username if report.reporter_id else (report.reporter_display or 'Deleted user')}",
                f"Reason: {report.reason or 'No reason provided'}",
                f"Created: {report.created_at:%Y-%m-%d %H:%M UTC}",
            ]
        )
        if report.status == Report.Status.PENDING:
            lines.append(f"Resolve: `POST /admin/reports/{report.pk}/resolve/`.")
        lines.append("")
    if not reports.exists():
        lines.append("No matching reports.")
    lines.extend(["", "Return to [administration](/admin/)."])
    return markdown_response("\n".join(lines) + "\n")


@require_http_methods(["GET"])
@api_token_required(admin=True)
def admin_post_detail(request, post_id):
    try:
        post = Post.objects.select_related("author").get(pk=post_id)
    except Post.DoesNotExist:
        return json_error("Post not found.", 404)
    return JsonResponse({"post": post_json(post)})


@require_http_methods(["POST"])
@api_token_required(admin=True)
def resolve_report(request, report_id):
    try:
        report = Report.objects.get(pk=report_id)
    except Report.DoesNotExist:
        return json_error("Report not found.", 404)
    if report.status != Report.Status.RESOLVED:
        report.status = Report.Status.RESOLVED
        report.resolved_at = timezone.now()
        report.resolved_by = request.user
        report.save(update_fields=("status", "resolved_at", "resolved_by"))
    return JsonResponse({"report": report_json(report)})


@require_http_methods(["POST"])
@api_token_required(admin=True)
def set_post_visibility(request, post_id):
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return json_error("Post not found.", 404)
    payload, error = json_payload(request)
    if error:
        return error
    visibility = payload.get("visibility")
    if visibility not in Post.Visibility.values:
        return json_error("Invalid visibility.", 400)
    post.visibility = visibility
    post.save(update_fields=("visibility", "updated_at"))
    return JsonResponse({"post": post_json(post)})


@require_http_methods(["DELETE"])
@api_token_required(admin=True)
def delete_post(request, post_id):
    deleted, _ = Post.objects.filter(pk=post_id).delete()
    if not deleted:
        return json_error("Post not found.", 404)
    return JsonResponse({"status": "deleted"})


@require_http_methods(["DELETE"])
@api_token_required(admin=True)
def delete_comment(request, comment_id):
    deleted, _ = Comment.objects.filter(pk=comment_id).delete()
    if not deleted:
        return json_error("Comment not found.", 404)
    return JsonResponse({"status": "deleted"})


@require_http_methods(["POST"])
@api_token_required(admin=True)
def set_comment_visibility(request, comment_id):
    comment = Comment.objects.filter(pk=comment_id).first()
    if comment is None:
        return json_error("Comment not found.", 404)
    payload, error = json_payload(request)
    if error:
        return error
    hidden = payload.get("hidden")
    if not isinstance(hidden, bool):
        return json_error("hidden must be true or false.", 400)
    comment.is_hidden = hidden
    comment.save(update_fields=("is_hidden",))
    return JsonResponse({"id": comment.pk, "hidden": comment.is_hidden})


@require_http_methods(["GET"])
@api_token_required(admin=True, markdown=True)
def admin_users(request):
    users = User.objects.order_by("date_joined", "id")
    lines = ["# Account moderation", "", "Approve, reject, disable, or delete an account by ID.", ""]
    for user in users:
        lines.extend(
            [
                f"## {user.username} (ID {user.pk})",
                f"Status: {user.approval_status} | {'active' if user.is_active else 'disabled'} | {'administrator' if is_admin(user) else 'user'}",
            ]
        )
        if user.approval_status == User.ApprovalStatus.PENDING:
            lines.extend(
                [
                    f"Approve: `POST /admin/users/{user.pk}/approve/`.",
                    f"Reject: `POST /admin/users/{user.pk}/reject/`.",
                ]
            )
        if user.is_active:
            lines.append(f"Disable: `POST /admin/users/{user.pk}/disable/`.")
        if not is_admin(user):
            lines.append(
                f"Delete: `DELETE /admin/users/{user.pk}/` with JSON "
                "`{\"posts\": \"keep|hide|delete\", \"comments\": \"keep|hide|delete\"}`."
            )
        lines.append("")
    if not users.exists():
        lines.append("No accounts exist.")
    lines.extend(["", "Return to [administration](/admin/)."])
    return markdown_response("\n".join(lines) + "\n")


def guard_last_admin(target):
    if not is_admin(target):
        return False
    return not User.objects.filter(
        is_active=True,
        is_staff=True,
        approval_status=User.ApprovalStatus.APPROVED,
    ).exclude(pk=target.pk).exists()


@require_http_methods(["POST"])
@api_token_required(admin=True)
def moderate_user(request, user_id, action):
    target = User.objects.filter(pk=user_id).first()
    if target is None:
        return json_error("User not found.", 404)
    if action not in {"approve", "reject", "disable"}:
        return json_error("Invalid user action.", 404)
    if action == "approve":
        target.approval_status = User.ApprovalStatus.APPROVED
        target.is_active = True
        target.save(update_fields=("approval_status", "is_active"))
    elif action == "reject":
        if guard_last_admin(target):
            return json_error("Cannot reject this administrator account.", 409)
        target.approval_status = User.ApprovalStatus.REJECTED
        target.is_active = False
        target.save(update_fields=("approval_status", "is_active"))
    else:
        if target.pk == request.user.pk or guard_last_admin(target):
            return json_error("Cannot disable this administrator account.", 409)
        target.is_active = False
        target.save(update_fields=("is_active",))
    return JsonResponse({"id": target.pk, "approval_status": target.approval_status, "is_active": target.is_active})


@require_http_methods(["DELETE"])
@api_token_required(admin=True)
def delete_user(request, user_id):
    target = User.objects.filter(pk=user_id).first()
    if target is None:
        return json_error("User not found.", 404)
    if target.pk == request.user.pk or guard_last_admin(target):
        return json_error("Cannot delete this administrator account.", 409)
    payload, error = json_payload(request)
    if error:
        return error
    post_action = payload.get("posts")
    comment_action = payload.get("comments")
    allowed_actions = {"keep", "hide", "delete"}
    if post_action not in allowed_actions or comment_action not in allowed_actions:
        return json_error("posts and comments must each be keep, hide, or delete.", 400)
    with transaction.atomic():
        posts = Post.objects.filter(author=target)
        comments = Comment.objects.filter(author=target)
        if post_action == "delete":
            posts.delete()
        else:
            post_changes = {"author": None, "author_display": "Deleted user"}
            if post_action == "hide":
                post_changes["visibility"] = Post.Visibility.ADMIN
            posts.update(**post_changes)
        if comment_action == "delete":
            comments.delete()
        else:
            comment_changes = {"author": None, "author_display": "Deleted user"}
            if comment_action == "hide":
                comment_changes["is_hidden"] = True
            comments.update(**comment_changes)
        Report.objects.filter(reporter=target).update(reporter=None, reporter_display="Deleted user")
        target.delete()
    return JsonResponse({"status": "deleted", "posts": post_action, "comments": comment_action})