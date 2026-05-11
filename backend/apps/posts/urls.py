from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminCommentMarkReadAPIView,
    AdminCommentReplyAPIView,
    AdminUnreadCommentCountAPIView,
    AdminUnreadCommentListAPIView,
    CommentDestroyAPIView,
    CommentListCreateAPIView,
    PostViewSet,
    SiteProfileAdminAPIView,
    SiteProfilePublicAPIView,
)

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="posts")

urlpatterns = [
    path("", include(router.urls)),
    path("profile/", SiteProfilePublicAPIView.as_view(), name="site-profile-public"),
    path(
        "admin/profile/",
        SiteProfileAdminAPIView.as_view(),
        name="site-profile-admin",
    ),
    path(
        "posts/<int:post_id>/comments/",
        CommentListCreateAPIView.as_view(),
        name="post-comments",
    ),
    path("comments/<int:pk>/", CommentDestroyAPIView.as_view(), name="comment-delete"),
    path(
        "admin/comments/unread/count/",
        AdminUnreadCommentCountAPIView.as_view(),
        name="admin-unread-comment-count",
    ),
    path(
        "admin/comments/unread/",
        AdminUnreadCommentListAPIView.as_view(),
        name="admin-unread-comment-list",
    ),
    path(
        "admin/comments/<int:pk>/reply/",
        AdminCommentReplyAPIView.as_view(),
        name="admin-comment-reply",
    ),
    path(
        "admin/comments/<int:pk>/read/",
        AdminCommentMarkReadAPIView.as_view(),
        name="admin-comment-read",
    ),
]
