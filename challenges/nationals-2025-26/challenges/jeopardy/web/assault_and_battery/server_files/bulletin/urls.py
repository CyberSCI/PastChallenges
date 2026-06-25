from rest_framework.routers import DefaultRouter

from bulletin.views import BulletinPostViewSet, BulletinViewSet, CommentViewSet

router = DefaultRouter()
router.register(r"posts", BulletinPostViewSet, basename="posts")
router.register(r"comments", CommentViewSet, basename="comments")
router.register(r"", BulletinViewSet, basename="bulletin")

urlpatterns = router.urls
