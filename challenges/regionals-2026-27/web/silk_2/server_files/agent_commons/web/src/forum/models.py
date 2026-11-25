from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


class User(AbstractUser):
    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    approval_status = models.CharField(
        max_length=12,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Post(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        AUTHENTICATED = "authenticated", "Authenticated users"
        ADMIN = "admin", "Admins only"

    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="posts")
    author_display = models.CharField(max_length=150, blank=True, default="")
    title = models.CharField(max_length=200)
    body = models.TextField()
    visibility = models.CharField(max_length=16, choices=Visibility.choices, default=Visibility.PUBLIC, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [models.Index(fields=("visibility", "-created_at", "-id"), name="post_vis_created_idx")]

    def display_author(self):
        return self.author.username if self.author_id else (self.author_display or "Deleted user")


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="comments")
    author_display = models.CharField(max_length=150, blank=True, default="")
    body = models.TextField()
    is_hidden = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")

    def display_author(self):
        return self.author.username if self.author_id else (self.author_display or "Deleted user")


class Report(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RESOLVED = "resolved", "Resolved"

    url = models.CharField(max_length=2048)
    reporter = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="reports")
    reporter_display = models.CharField(max_length=150, blank=True, default="")
    reason = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resolved_reports",
    )

    class Meta:
        ordering = ("created_at", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("url", "reporter"),
                condition=Q(status="pending"),
                name="uniq_pending_reporter_url",
            )
        ]
        indexes = [models.Index(fields=("status", "created_at", "id"), name="report_status_created_idx")]