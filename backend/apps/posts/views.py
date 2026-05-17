from django.conf import settings
from django.contrib.auth import authenticate
from django.db.models import F
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import AnnouncementMedia, BlockedKeyword, Comment, ContentReview, Like, Message, Music, Post, PostMedia, SiteAnnouncement, SiteProfile, TimelineMedia
from .moderation import moderate_nickname, moderate_text
from .serializers import (
    BlockedKeywordSerializer,
    CommentAdminSerializer,
    CommentReplySerializer,
    CommentSerializer,
    ContentReviewSerializer,
    MessageSerializer,
    MusicSerializer,
    MusicWriteSerializer,
    PostMediaSerializer,
    PostSerializer,
    PostWriteSerializer,
    SiteAnnouncementSerializer,
    SiteProfileAdminSerializer,
    SiteProfilePublicSerializer,
    TimelineMediaSerializer,
    TimelineMediaWriteSerializer,
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
        if content_type.startswith("audio/"):
            return Post.MEDIA_TYPE_AUDIO
        return Post.MEDIA_TYPE_NONE

    def _infer_post_media_type(self, file_obj):
        content_type = getattr(file_obj, "content_type", "") or ""
        if content_type.startswith("image/"):
            return PostMedia.MEDIA_TYPE_IMAGE
        if content_type.startswith("video/"):
            return PostMedia.MEDIA_TYPE_VIDEO
        if content_type.startswith("audio/"):
            return PostMedia.MEDIA_TYPE_AUDIO
        return PostMedia.MEDIA_TYPE_FILE

    def perform_create(self, serializer):
        post = serializer.save(media_type=Post.MEDIA_TYPE_NONE)
        files = self.request.FILES.getlist("files")
        if files:
            for f in files:
                PostMedia.objects.create(
                    post=post,
                    file=f,
                    media_type=self._infer_post_media_type(f),
                )
            return
        single = serializer.validated_data.get("media")
        if single:
            PostMedia.objects.create(
                post=post,
                file=single,
                media_type=self._infer_post_media_type(single),
            )
            return
        media_type = serializer.validated_data.get("media_type") or Post.MEDIA_TYPE_NONE
        post.media_type = self._infer_media_type(serializer.validated_data.get("media"), media_type)
        post.save(update_fields=["media_type"])

    def perform_update(self, serializer):
        post = serializer.save()
        files = self.request.FILES.getlist("files")
        if files:
            for f in files:
                PostMedia.objects.create(
                    post=post,
                    file=f,
                    media_type=self._infer_post_media_type(f),
                )
        single = serializer.validated_data.get("media")
        if single:
            PostMedia.objects.create(
                post=post, file=single, media_type=self._infer_post_media_type(single)
            )
        media_type = serializer.validated_data.get("media_type") or Post.MEDIA_TYPE_NONE
        post.media_type = self._infer_media_type(serializer.validated_data.get("media"), media_type)
        post.save(update_fields=["media_type"])

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

    @action(detail=True, methods=["post"], permission_classes=(permissions.IsAdminUser,))
    def pin(self, request, pk=None):
        post = self.get_object()
        post.is_pinned = not post.is_pinned
        post.save(update_fields=["is_pinned"])
        return Response({"id": post.id, "is_pinned": post.is_pinned})


class PostMediaDestroyView(APIView):
    permission_classes = (permissions.IsAdminUser,)

    def delete(self, request, post_id: int, pk: int):
        instance = get_object_or_404(PostMedia, pk=pk, post_id=post_id)
        instance.delete()
        remaining = PostMedia.objects.filter(post_id=post_id).count()
        if remaining == 0:
            post = Post.objects.get(pk=post_id)
            post.media = None
            post.media_type = Post.MEDIA_TYPE_NONE
            post.save(update_fields=["media", "media_type"])
        return Response({"remaining": remaining})


class CommentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        post_id = self.kwargs["post_id"]
        return Comment.objects.filter(post_id=post_id, review_status="approved")

    def perform_create(self, serializer):
        post_id = self.kwargs["post_id"]
        post = get_object_or_404(Post, pk=post_id)
        parent = serializer.validated_data.get("parent")
        if parent is not None and parent.post_id != post.id:
            raise ValidationError("Parent comment must belong to the same post")

        nickname = serializer.validated_data.get("nickname", "")
        content = serializer.validated_data.get("content", "")

        # 审核昵称
        nick_action, nick_reason = moderate_nickname(nickname)
        if nick_action == "block":
            raise ValidationError({"detail": nick_reason})

        # 审核内容
        action, reason = moderate_text(content)
        if action == "block":
            raise ValidationError({"detail": reason})

        review_status = "pending" if (action == "review" or nick_action == "review") else "approved"

        comment = serializer.save(
            post=post, ip_address=get_client_ip(self.request), is_unread=True, review_status=review_status
        )

        if review_status == "pending":
            from django.utils import timezone
            ContentReview.objects.create(
                review_type="comment",
                source_id=comment.id,
                nickname=nickname,
                content=content,
                ai_reason=reason or nick_reason,
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


class AIChatView(APIView):
    permission_classes = (permissions.AllowAny,)
    parser_classes = (JSONParser,)

    def _build_site_context(self) -> str:
        parts = []

        # 1. 网站概况
        profile = SiteProfile.get_solo()
        parts.append(f"网站主人昵称：{profile.nickname}")
        parts.append(f"个性签名：{profile.bio or '（无）'}")

        # 2. 动态
        posts = Post.objects.all().order_by("-created_at")[:20]
        parts.append(f"\n主人共发布了 {Post.objects.count()} 条动态，最近 20 条：")
        for p in posts:
            date_str = p.created_at.strftime("%Y-%m-%d %H:%M")
            txt = (p.content[:150] + "…") if len(p.content) > 150 else p.content
            parts.append(f"- {date_str} {txt}")

        # 3. 音乐
        music_count = Music.objects.count()
        if music_count:
            parts.append(f"\n主人上传了 {music_count} 首音乐：")
            for m in Music.objects.all().order_by("-created_at")[:10]:
                parts.append(f"- 《{m.title}》by {m.artist}（{m.duration:.0f}秒）")

        # 4. 留言板
        msg_count = Message.objects.count()
        if msg_count:
            parts.append(f"\n留言板共有 {msg_count} 条留言，最近 10 条：")
            for m in Message.objects.all().order_by("-created_at")[:10]:
                parts.append(f"- {m.nickname}：{m.content[:80]}")

        # 5. 时光相册
        timeline_count = TimelineMedia.objects.count()
        if timeline_count:
            parts.append(f"\n时光相册有 {timeline_count} 张照片/视频")

        # 6. 动态评论（公开的）
        from .models import Comment
        comment_count = Comment.objects.count()
        if comment_count:
            parts.append(f"\n动态共有 {comment_count} 条公开评论")

        return "\n".join(parts) if parts else "该网站目前还没有内容。"

    def post(self, request):
        message = request.data.get("message", "").strip()
        history = request.data.get("history", [])

        if not message:
            return Response(
                {"reply": "请说点什么吧～"}, status=status.HTTP_200_OK
            )

        api_key = getattr(settings, "DEEPSEEK_API_KEY", "")

        if api_key:
            reply = self._call_deepseek(message, history, api_key)
        else:
            reply = self._simple_chat(message)

        return Response({"reply": reply})

    def _call_deepseek(self, message: str, history: list, api_key: str) -> str:
        import requests

        site_context = self._build_site_context()

        system_prompt = {
            "role": "system",
            "content": (
                "你是一个温暖、友善的树洞 AI 助手，名字叫「树洞小助手」。"
                "你陪伴用户聊天、倾听他们的心事、给出温暖的回应。"
                "回答简洁自然，使用中文，语气亲切。"
                "你非常了解这个网站和网站的主人，因为你能看到网站的所有公开信息，包括动态、音乐、留言、相册等。"
                "如果用户问起网站或主人的事情，你可以根据下面的网站信息来回答。"
                "你不知道的事情不要瞎编，可以说'这个我还不清楚呢'。"
                "如果用户问的是网站以外的事情（比如日常生活、知识问答、技术问题等），你也要正常回答，不要限制自己。"
                "你唯一不能透露的是管理员登录、密码、安全相关的信息。"
                f"\n\n【网站信息】\n{site_context}"
            ),
        }

        messages = [system_prompt]
        for h in history[-10:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": message})

        try:
            resp = requests.post(
                getattr(settings, "DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": getattr(settings, "AI_MODEL", "deepseek-chat"),
                    "messages": messages,
                    "temperature": 0.8,
                    "max_tokens": 1024,
                },
                timeout=30,
            )
            data = resp.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"].strip()
            return "AI 暂时无法回答，请稍后再试～"
        except Exception as e:
            return f"哎呀，AI 走神了：{str(e)[:100]}"

    def _simple_chat(self, message: str) -> str:
        import random

        msg = message.lower()

        if any(kw in msg for kw in ["你好", "嗨", "hi", "hello", "在吗"]):
            return "你好呀～ 欢迎来到树洞，我是你的专属小助手 😊\n有什么想聊的、想倾诉的都可以跟我说～"

        if any(kw in msg for kw in ["心情", "难过", "不开心", "郁闷", "烦"]):
            return "抱抱你～ 不开心的事情说出来会好受一些，我在这里听着呢。"

        if any(kw in msg for kw in ["开心", "高兴", "快乐", "哈哈", "棒"]):
            return "哇，为你开心！🎉 分享快乐会让快乐加倍哦～"

        if any(kw in msg for kw in ["名字", "是谁", "你叫"]):
            return "我是树洞小助手，你的专属聆听者～ 🌳"

        if any(kw in msg for kw in ["谢谢", "感谢"]):
            return "不用谢～ 能陪你聊天我也很开心！💛"

        replies = [
            "嗯嗯，继续说说你的想法吧～",
            "我在听呢，请继续说～ 👂",
            "这个角度很有意思，展开讲讲？",
            "你说得对，我也有同感！",
            "原来如此～ 那后来呢？",
            "哇，好有趣！再跟我多聊聊吧～",
        ]
        return random.choice(replies)


class TimelineMediaListCreateView(generics.ListCreateAPIView):
    queryset = TimelineMedia.objects.all()
    permission_classes = (permissions.AllowAny,)
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return TimelineMediaSerializer
        return TimelineMediaWriteSerializer

    def get_serializer_context(self):
        return {"request": self.request}


class AdminLoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    parser_classes = (JSONParser,)

    def post(self, request):
        username = request.data.get("username", "")
        password = request.data.get("password", "")

        if not username or not password:
            return Response(
                {"detail": "请输入用户名和密码"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)

        if user is None or not user.is_staff:
            return Response(
                {"detail": "账号或密码错误，或无管理员权限"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        import secrets
        token_hex = secrets.token_hex(32)
        profile = SiteProfile.get_solo()
        profile.session_token = token_hex
        profile.save(update_fields=["session_token"])

        refresh = RefreshToken.for_user(user)
        refresh["session_token"] = token_hex

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })


class MusicListAPIView(generics.ListCreateAPIView):
    queryset = Music.objects.all()
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return MusicSerializer
        return MusicWriteSerializer

    def get_serializer_context(self):
        return {"request": self.request}

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def perform_create(self, serializer):
        serializer.save()


class MusicDestroyAPIView(generics.DestroyAPIView):
    queryset = Music.objects.all()
    serializer_class = MusicSerializer
    permission_classes = (permissions.IsAdminUser,)


class MessageListCreateAPIView(generics.ListCreateAPIView):
    queryset = Message.objects.filter(review_status="approved")
    serializer_class = MessageSerializer
    permission_classes = (permissions.AllowAny,)

    def perform_create(self, serializer):
        nickname = serializer.validated_data.get("nickname", "")
        content = serializer.validated_data.get("content", "")

        nick_action, nick_reason = moderate_nickname(nickname)
        if nick_action == "block":
            raise ValidationError({"detail": nick_reason})

        action, reason = moderate_text(content)
        if action == "block":
            raise ValidationError({"detail": reason})

        review_status = "pending" if (action == "review" or nick_action == "review") else "approved"

        msg = serializer.save(review_status=review_status)

        if review_status == "pending":
            ContentReview.objects.create(
                review_type="message",
                source_id=msg.id,
                nickname=nickname,
                content=content,
                ai_reason=reason or nick_reason,
            )


class MessageDestroyAPIView(generics.DestroyAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = (permissions.IsAdminUser,)


class TimelineMediaDestroyView(generics.DestroyAPIView):
    queryset = TimelineMedia.objects.all()
    permission_classes = (permissions.IsAdminUser,)


class TimelineMediaDetailView(generics.RetrieveUpdateAPIView):
    queryset = TimelineMedia.objects.all()
    permission_classes = (permissions.IsAdminUser,)
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return TimelineMediaSerializer
        return TimelineMediaWriteSerializer

    def get_serializer_context(self):
        return {"request": self.request}


class BlockedKeywordListCreateView(generics.ListCreateAPIView):
    queryset = BlockedKeyword.objects.all()
    serializer_class = BlockedKeywordSerializer
    permission_classes = (permissions.IsAdminUser,)


class BlockedKeywordDestroyView(generics.DestroyAPIView):
    queryset = BlockedKeyword.objects.all()
    permission_classes = (permissions.IsAdminUser,)


class SiteAnnouncementPublicView(generics.ListAPIView):
    queryset = SiteAnnouncement.objects.filter(is_active=True).prefetch_related("media_items")
    serializer_class = SiteAnnouncementSerializer
    permission_classes = (permissions.AllowAny,)

    def get_serializer_context(self):
        return {"request": self.request}


class SiteAnnouncementListCreateView(generics.ListCreateAPIView):
    queryset = SiteAnnouncement.objects.all().prefetch_related("media_items")
    serializer_class = SiteAnnouncementSerializer
    permission_classes = (permissions.IsAdminUser,)
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_serializer_context(self):
        return {"request": self.request}

    def _infer_media_type(self, file_obj):
        content_type = getattr(file_obj, "content_type", "") or ""
        if content_type.startswith("image/"):
            return AnnouncementMedia.MEDIA_TYPE_IMAGE
        if content_type.startswith("video/"):
            return AnnouncementMedia.MEDIA_TYPE_VIDEO
        if content_type.startswith("audio/"):
            return AnnouncementMedia.MEDIA_TYPE_AUDIO
        return AnnouncementMedia.MEDIA_TYPE_FILE

    def perform_create(self, serializer):
        announcement = serializer.save()
        files = self.request.FILES.getlist("files")
        if files:
            for f in files:
                AnnouncementMedia.objects.create(
                    announcement=announcement,
                    file=f,
                    media_type=self._infer_media_type(f),
                )


class SiteAnnouncementDestroyView(generics.DestroyAPIView):
    queryset = SiteAnnouncement.objects.all()
    serializer_class = SiteAnnouncementSerializer
    permission_classes = (permissions.IsAdminUser,)


class SiteAnnouncementUpdateView(generics.RetrieveUpdateAPIView):
    queryset = SiteAnnouncement.objects.all().prefetch_related("media_items")
    serializer_class = SiteAnnouncementSerializer
    permission_classes = (permissions.IsAdminUser,)
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_serializer_context(self):
        return {"request": self.request}

    def _infer_media_type(self, file_obj):
        content_type = getattr(file_obj, "content_type", "") or ""
        if content_type.startswith("image/"):
            return AnnouncementMedia.MEDIA_TYPE_IMAGE
        if content_type.startswith("video/"):
            return AnnouncementMedia.MEDIA_TYPE_VIDEO
        if content_type.startswith("audio/"):
            return AnnouncementMedia.MEDIA_TYPE_AUDIO
        return AnnouncementMedia.MEDIA_TYPE_FILE

    def perform_update(self, serializer):
        announcement = serializer.save()
        files = self.request.FILES.getlist("files")
        if files:
            announcement.media_items.all().delete()
            for f in files:
                AnnouncementMedia.objects.create(
                    announcement=announcement,
                    file=f,
                    media_type=self._infer_media_type(f),
                )


class ContentReviewListAPIView(generics.ListAPIView):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ContentReviewSerializer

    def get_queryset(self):
        return ContentReview.objects.filter(status="pending")


class ContentReviewCountAPIView(APIView):
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        count = ContentReview.objects.filter(status="pending").count()
        return Response({"count": count})


class ContentReviewApproveAPIView(APIView):
    permission_classes = (permissions.IsAdminUser,)

    def post(self, request, pk: int):
        review = get_object_or_404(ContentReview, pk=pk)
        if review.status != "pending":
            return Response({"detail": "该审核项已处理"}, status=400)

        review.status = "approved"
        review.reviewed_at = timezone.now()
        review.save(update_fields=["status", "reviewed_at"])

        if review.review_type == "comment":
            Comment.objects.filter(pk=review.source_id).update(review_status="approved")
        elif review.review_type == "message":
            Message.objects.filter(pk=review.source_id).update(review_status="approved")

        return Response({"id": review.id, "status": "approved"})


class ContentReviewRejectAPIView(APIView):
    permission_classes = (permissions.IsAdminUser,)

    def post(self, request, pk: int):
        review = get_object_or_404(ContentReview, pk=pk)
        if review.status != "pending":
            return Response({"detail": "该审核项已处理"}, status=400)

        review.status = "rejected"
        review.reviewed_at = timezone.now()
        review.save(update_fields=["status", "reviewed_at"])

        if review.review_type == "comment":
            Comment.objects.filter(pk=review.source_id).delete()
        elif review.review_type == "message":
            Message.objects.filter(pk=review.source_id).delete()

        return Response({"id": review.id, "status": "rejected"})
