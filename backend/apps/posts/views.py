from django.db.models import F
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import Comment, Like, Post, PostMedia, SiteProfile
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

    def _infer_media_type(self, file_obj):
        content_type = getattr(file_obj, "content_type", "") or ""
        if content_type.startswith("image/"):
            return Post.MEDIA_TYPE_IMAGE
        if content_type.startswith("video/"):
            return Post.MEDIA_TYPE_VIDEO
        if content_type.startswith("audio/"):
            return Post.MEDIA_TYPE_AUDIO
        name = getattr(file_obj, "name", "") or ""
        ext = name.split(".")[-1].lower() if "." in name else ""
        if ext in {"mp3", "wav", "m4a", "aac", "ogg", "webm"}:
            return Post.MEDIA_TYPE_AUDIO
        if ext in {"mp4", "mov", "webm", "mkv"}:
            return Post.MEDIA_TYPE_VIDEO
        if ext in {"png", "jpg", "jpeg", "gif", "webp"}:
            return Post.MEDIA_TYPE_IMAGE
        return Post.MEDIA_TYPE_FILE

    def _save_media_items(self, post: Post, files):
        for f in files:
            PostMedia.objects.create(
                post=post, file=f, media_type=self._infer_media_type(f)
            )

        first = post.media_items.first()
        if first:
            post.media_type = first.media_type
            post.save(update_fields=["media_type"])

    def create(self, request, *args, **kwargs):
        content = (request.data.get("content") or "").strip()
        files = request.FILES.getlist("media")
        if not content and not files:
            return Response({"detail": "empty"}, status=status.HTTP_400_BAD_REQUEST)

        post = Post.objects.create(content=content, media_type=Post.MEDIA_TYPE_NONE)
        self._save_media_items(post, files)
        serializer = PostSerializer(post, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        post = self.get_object()
        if "content" in request.data:
            post.content = (request.data.get("content") or "").strip()
            post.save(update_fields=["content"])

        replace_media = str(request.data.get("replace_media") or "").lower() in {
            "1",
            "true",
            "yes",
        }
        files = request.FILES.getlist("media")
        if replace_media:
            post.media_items.all().delete()
            post.media = None
            post.media_type = Post.MEDIA_TYPE_NONE
            post.save(update_fields=["media", "media_type"])

        if files:
            self._save_media_items(post, files)

        serializer = PostSerializer(post, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)

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
