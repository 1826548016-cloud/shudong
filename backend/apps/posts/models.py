from django.db import models

class Post(models.Model):
    MEDIA_TYPE_NONE = "none"
    MEDIA_TYPE_IMAGE = "image"
    MEDIA_TYPE_VIDEO = "video"
    MEDIA_TYPE_AUDIO = "audio"
    MEDIA_TYPE_FILE = "file"

    MEDIA_TYPE_CHOICES = (
        (MEDIA_TYPE_NONE, "None"),
        (MEDIA_TYPE_IMAGE, "Image"),
        (MEDIA_TYPE_VIDEO, "Video"),
        (MEDIA_TYPE_AUDIO, "Audio"),
        (MEDIA_TYPE_FILE, "File"),
    )

    content = models.TextField(blank=True)
    media = models.FileField(upload_to="posts/", blank=True, null=True)
    media_type = models.CharField(
        max_length=10, choices=MEDIA_TYPE_CHOICES, default=MEDIA_TYPE_NONE
    )
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class PostMedia(models.Model):
    post = models.ForeignKey(Post, related_name="media_items", on_delete=models.CASCADE)
    file = models.FileField(upload_to="posts/")
    media_type = models.CharField(
        max_length=10, choices=Post.MEDIA_TYPE_CHOICES, default=Post.MEDIA_TYPE_FILE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class Comment(models.Model):
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    nickname = models.CharField(max_length=32, blank=True)
    content = models.CharField(max_length=500)
    admin_reply = models.CharField(max_length=500, blank=True)
    replied_at = models.DateTimeField(blank=True, null=True)
    is_unread = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Like(models.Model):
    post = models.ForeignKey(Post, related_name="likes", on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "ip_address"], name="uniq_like_post_ip"
            )
        ]


class SiteProfile(models.Model):
    nickname = models.CharField(max_length=32, default="树洞主人")
    avatar = models.ImageField(upload_to="profile/", blank=True, null=True)
    bio = models.CharField(max_length=200, blank=True)
    wechat_id = models.CharField(max_length=64, blank=True)
    douyin_url = models.URLField(blank=True)
    phone_num = models.CharField(max_length=32, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_solo(cls):
        obj = cls.objects.first()
        if obj:
            return obj
        return cls.objects.create()
