from django.db.models import F
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import Comment, Like, Post, SiteProfile
from .serializers import (
    CommentAdminSerializer,
    CommentReplySerializer,
    CommentSerializer,
    PostSerializer,
    PostWriteSerializer,
    SiteProfileAdminSerializer,
    SiteProfilePublicSerializer,
)


def get_client_ip(request) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or "0.0.0.0"


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = getattr(request, "user", None)
        return bool(user and user.is_staff)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = (IsAdminOrReadOnly,)
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return PostWriteSerializer
        return PostSerializer

    def get_serializer_context(self):
        return {"request": self.request}

    def _infer_media_type(self, file_obj, current: str):
        if file_obj is None or current and current != Post.MEDIA_TYPE_NONE:
            return current
        content_type = getattr(file_obj, "content_type", "") or ""
        if content_type.startswith("image/"):
            return Post.MEDIA_TYPE_IMAGE
        if content_type.startswith("video/"):
            return Post.MEDIA_TYPE_VIDEO
        return Post.MEDIA_TYPE_NONE

    def perform_create(self, serializer):
        media = serializer.validated_data.get("media")
        media_type = serializer.validated_data.get("media_type") or Post.MEDIA_TYPE_NONE
        serializer.save(media_type=self._infer_media_type(media, media_type))

    def perform_update(self, serializer):
        media = serializer.validated_data.get("media")
        media_type = serializer.validated_data.get("media_type") or Post.MEDIA_TYPE_NONE
        serializer.save(media_type=self._infer_media_type(media, media_type))

    @action(detail=True, methods=["post"], permission_classes=(permissions.AllowAny,))
    def view(self, request, pk=None):
        post = self.get_object()
        Post.objects.filter(pk=post.pk).update(view_count=F("view_count") + 1)
        post.refresh_from_db(fields=["view_count"])
        return Response({"id": post.id, "view_count": post.view_count})

    @action(detail=True, methods=["post"], permission_classes=(permissions.AllowAny,))
    def like(self, request, pk=None):
        post = self.get_object()
        ip = get_client_ip(request)

        like, created = Like.objects.get_or_create(post=post, ip_address=ip)
        if created:
            Post.objects.filter(pk=post.pk).update(like_count=F("like_count") + 1)
            post.refresh_from_db(fields=["like_count"])

        return Response(
            {"id": post.id, "like_count": post.like_count, "liked": True},
            status=status.HTTP_200_OK,
        )


class CommentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        post_id = self.kwargs["post_id"]
        return Comment.objects.filter(post_id=post_id)

    def perform_create(self, serializer):
        post_id = self.kwargs["post_id"]
        post = get_object_or_404(Post, pk=post_id)
        serializer.save(
            post=post, ip_address=get_client_ip(self.request), is_unread=True
        )


class CommentDestroyAPIView(generics.DestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAdminUser,)


class AdminUnreadCommentCountAPIView(APIView):
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        count = Comment.objects.filter(is_unread=True).count()
        return Response({"count": count})


class AdminUnreadCommentListAPIView(generics.ListAPIView):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = CommentAdminSerializer

    def get_queryset(self):
        return Comment.objects.filter(is_unread=True).select_related("post")


class AdminCommentReplyAPIView(APIView):
    permission_classes = (permissions.IsAdminUser,)
    parser_classes = (JSONParser, FormParser, MultiPartParser)

    def post(self, request, pk: int):
        comment = get_object_or_404(Comment, pk=pk)
        serializer = CommentReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin_reply = serializer.validated_data["admin_reply"].strip()

        comment.admin_reply = admin_reply
        comment.replied_at = timezone.now()
        comment.is_unread = False
        comment.save(update_fields=["admin_reply", "replied_at", "is_unread"])
        return Response(CommentSerializer(comment).data)


class AdminCommentMarkReadAPIView(APIView):
    permission_classes = (permissions.IsAdminUser,)

    def post(self, request, pk: int):
        comment = get_object_or_404(Comment, pk=pk)
        if comment.is_unread:
            comment.is_unread = False
            comment.save(update_fields=["is_unread"])
        return Response({"id": comment.id, "is_unread": comment.is_unread})


class SiteProfilePublicAPIView(generics.RetrieveAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = SiteProfilePublicSerializer

    def get_object(self):
        return SiteProfile.get_solo()


class SiteProfileAdminAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = SiteProfileAdminSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_object(self):
        return SiteProfile.get_solo()

    def get_serializer_context(self):
        return {"request": self.request}
