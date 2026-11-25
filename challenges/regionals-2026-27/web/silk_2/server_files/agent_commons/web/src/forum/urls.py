from django.urls import path

from forum import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("out/", views.outbound_redirect, name="outbound-redirect"),
    path("", views.post_index, name="home"),
    path("posts/page/<int:path_page>/", views.post_index, name="post-page"),
    path("register/", views.register, name="register"),
    path("login/", views.login, name="login"),
    path("account/", views.me, name="account"),
    path("posts/", views.posts_api, name="posts"),
    path("posts/<int:post_id>/", views.post_detail, name="post-detail"),
    path("posts/<int:post_id>/content/", views.post_content, name="post-content"),
    path("posts/<int:post_id>/comments/", views.create_comment, name="create-comment"),
    path("reports/", views.create_report, name="create-report"),
    path("posts/<int:post_id>/visibility/", views.set_post_visibility, name="set-post-visibility"),
    path("comments/<int:comment_id>/", views.delete_comment, name="delete-comment"),
    path("comments/<int:comment_id>/visibility/", views.set_comment_visibility, name="set-comment-visibility"),
    path("admin/", views.admin_home, name="admin-home"),
    path("admin/users/", views.admin_users, name="admin-users"),
    path("admin/users/<int:user_id>/<str:action>/", views.moderate_user, name="moderate-user"),
    path("admin/users/<int:user_id>/", views.delete_user, name="delete-user"),
    path("admin/posts/", views.admin_posts, name="admin-posts"),
    path("admin/reports/", views.admin_reports, name="admin-reports"),
    path("admin/reports/<int:report_id>/resolve/", views.resolve_report, name="resolve-report"),
]