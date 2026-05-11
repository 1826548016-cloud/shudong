from rest_framework import serializers

from .models import Comment, Post, SiteProfile


class PostSerializer(serializers.ModelSerializer):
    media_url = serializers.SerializerMethodField()
    comment_count = serializers.IntegerField(source="comments.count", read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "content",
            "media_url",
            "media_type",
            "view_count",
            "like_count",
            "comment_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "view_count",
            "like_count",
            "comment_count",
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
    class Meta:
        model = Comment
        fields = (
            "id",
            "post",
            "nickname",
            "content",
            "admin_reply",
            "replied_at",
            "created_at",
        )
        read_only_fields = ("id", "post", "admin_reply", "replied_at", "created_at")


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
    class Meta:
        model = SiteProfile
        fields = ("nickname", "bio", "wechat_id", "douyin_url")


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
