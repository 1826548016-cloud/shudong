from rest_framework import serializers

from .models import AnnouncementMedia, BlockedKeyword, Comment, ContentReview, Message, Music, Post, PostMedia, SiteAnnouncement, SiteProfile, TimelineMedia


class BlockedKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockedKeyword
        fields = ("id", "keyword", "created_at")
        read_only_fields = ("id", "created_at")


class PostMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = PostMedia
        fields = ("id", "file", "file_url", "media_type", "created_at")
        read_only_fields = ("id", "file_url", "created_at")

    def get_file_url(self, obj: PostMedia):
        if not obj.file:
            return None
        request = self.context.get("request")
        if request is None:
            return obj.file.url
        return request.build_absolute_uri(obj.file.url)


class PostSerializer(serializers.ModelSerializer):
    media_url = serializers.SerializerMethodField()
    comment_count = serializers.IntegerField(source="comments.count", read_only=True)
    media_items = PostMediaSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "content",
            "media_url",
            "media_type",
            "media_items",
            "view_count",
            "like_count",
            "comment_count",
            "is_pinned",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "view_count",
            "like_count",
            "comment_count",
            "is_pinned",
            "created_at",
            "updated_at",
        )

    def get_media_url(self, obj: Post):
        if not obj.media:
            return None
        request = self.context.get("request")
        if request is None:
            return obj.media.url
        return request.build_absolute_uri(obj.media.url)


class PostWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("content", "media", "media_type")


class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            "id",
            "post",
            "parent",
            "nickname",
            "content",
            "admin_reply",
            "replied_at",
            "replies",
            "created_at",
        )
        read_only_fields = ("id", "post", "admin_reply", "replied_at", "replies", "created_at")

    def get_replies(self, obj):
        replies = obj.replies.all()
        return CommentSerializer(replies, many=True, context=self.context).data


class CommentAdminSerializer(serializers.ModelSerializer):
    post_content = serializers.CharField(source="post.content", read_only=True)

    class Meta:
        model = Comment
        fields = (
            "id",
            "post",
            "post_content",
            "nickname",
            "content",
            "admin_reply",
            "replied_at",
            "is_unread",
            "created_at",
        )
        read_only_fields = ("id", "post", "post_content", "replied_at", "created_at")


class CommentReplySerializer(serializers.Serializer):
    admin_reply = serializers.CharField(max_length=500, allow_blank=True)


class SiteProfilePublicSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = SiteProfile
        fields = ("nickname", "bio", "wechat_id", "douyin_url", "email", "avatar_url")

    def get_avatar_url(self, obj: SiteProfile):
        if not obj.avatar:
            return None
        request = self.context.get("request")
        if request is None:
            return obj.avatar.url
        return request.build_absolute_uri(obj.avatar.url)


class AnnouncementMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = AnnouncementMedia
        fields = ("id", "file", "file_url", "media_type", "created_at")
        read_only_fields = ("id", "file_url", "created_at")

    def get_file_url(self, obj: AnnouncementMedia):
        if not obj.file:
            return None
        request = self.context.get("request")
        if request is None:
            return obj.file.url
        return request.build_absolute_uri(obj.file.url)


class SiteAnnouncementSerializer(serializers.ModelSerializer):
    media_items = AnnouncementMediaSerializer(many=True, read_only=True)

    class Meta:
        model = SiteAnnouncement
        fields = ("id", "title", "content", "is_active", "media_items", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at", "media_items")


class MusicSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Music
        fields = ("id", "title", "artist", "file", "file_url", "duration", "created_at")
        read_only_fields = ("id", "file_url", "duration", "created_at")

    def get_file_url(self, obj: Music):
        if not obj.file:
            return None
        request = self.context.get("request")
        if request is None:
            return obj.file.url
        return request.build_absolute_uri(obj.file.url)


class MusicWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Music
        fields = ("title", "artist", "file", "duration")
        read_only_fields = ("duration",)

    def create(self, validated_data):
        instance = super().create(validated_data)
        try:
            import mutagen
            file_path = instance.file.path
            audio = mutagen.File(file_path)
            if audio is not None and audio.info is not None:
                instance.duration = audio.info.length
                instance.save(update_fields=["duration"])
        except Exception:
            pass
        return instance


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ("id", "nickname", "content", "created_at")
        read_only_fields = ("id", "created_at")


class TimelineMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = TimelineMedia
        fields = (
            "id",
            "file",
            "file_url",
            "media_type",
            "caption",
            "shot_at",
            "created_at",
        )
        read_only_fields = ("id", "file_url", "created_at")

    def get_file_url(self, obj: TimelineMedia):
        if not obj.file:
            return None
        request = self.context.get("request")
        if request is None:
            return obj.file.url
        return request.build_absolute_uri(obj.file.url)


class TimelineMediaWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimelineMedia
        fields = ("file", "media_type", "caption", "shot_at")


class SiteProfileAdminSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = SiteProfile
        fields = (
            "nickname",
            "avatar",
            "avatar_url",
            "bio",
            "wechat_id",
            "douyin_url",
            "phone_num",
            "email",
            "updated_at",
        )
        read_only_fields = ("avatar_url", "updated_at")

    def get_avatar_url(self, obj: SiteProfile):
        if not obj.avatar:
            return None
        request = self.context.get("request")
        if request is None:
            return obj.avatar.url
        return request.build_absolute_uri(obj.avatar.url)


class ContentReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentReview
        fields = ("id", "review_type", "source_id", "nickname", "content", "ai_reason", "status", "created_at", "reviewed_at")
        read_only_fields = ("id", "created_at", "reviewed_at")
