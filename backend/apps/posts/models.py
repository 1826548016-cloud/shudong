from django.db import models

class Post(models.Model):
    MEDIA_TYPE_NONE = "none"
    MEDIA_TYPE_IMAGE = "image"
    MEDIA_TYPE_VIDEO = "video"
    MEDIA_TYPE_AUDIO = "audio"

    MEDIA_TYPE_CHOICES = (
        (MEDIA_TYPE_NONE, "None"),
        (MEDIA_TYPE_IMAGE, "Image"),
        (MEDIA_TYPE_VIDEO, "Video"),
        (MEDIA_TYPE_AUDIO, "Audio"),
    )

    content = models.TextField(blank=True)
    media = models.FileField(upload_to="posts/", blank=True, null=True)
    media_type = models.CharField(
        max_length=10, choices=MEDIA_TYPE_CHOICES, default=MEDIA_TYPE_NONE
    )
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]


class Comment(models.Model):
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    parent = models.ForeignKey(
        "self", related_name="replies", on_delete=models.CASCADE, null=True, blank=True
    )
    nickname = models.CharField(max_length=32, blank=True)
    content = models.CharField(max_length=500)
    admin_reply = models.CharField(max_length=500, blank=True)
    replied_at = models.DateTimeField(blank=True, null=True)
    is_unread = models.BooleanField(default=True)
    review_status = models.CharField(
        max_length=10,
        choices=(("approved", "Approved"), ("pending", "Pending"), ("rejected", "Rejected")),
        default="approved",
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


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
    email = models.CharField(max_length=128, blank=True)
    session_token = models.CharField(max_length=64, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_solo(cls):
        obj = cls.objects.first()
        if obj:
            return obj
        return cls.objects.create()


class TimelineMedia(models.Model):
    MEDIA_TYPE_IMAGE = "image"
    MEDIA_TYPE_VIDEO = "video"
    MEDIA_TYPE_CHOICES = (
        (MEDIA_TYPE_IMAGE, "Image"),
        (MEDIA_TYPE_VIDEO, "Video"),
    )

    file = models.FileField(upload_to="timeline/")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    caption = models.CharField(max_length=200, blank=True)
    shot_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-shot_at"]


class Music(models.Model):
    title = models.CharField(max_length=128)
    artist = models.CharField(max_length=64, blank=True, default="未知艺术家")
    file = models.FileField(upload_to="music/")
    duration = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class PostMedia(models.Model):
    MEDIA_TYPE_IMAGE = "image"
    MEDIA_TYPE_VIDEO = "video"
    MEDIA_TYPE_AUDIO = "audio"
    MEDIA_TYPE_FILE = "file"

    MEDIA_TYPE_CHOICES = (
        (MEDIA_TYPE_IMAGE, "Image"),
        (MEDIA_TYPE_VIDEO, "Video"),
        (MEDIA_TYPE_AUDIO, "Audio"),
        (MEDIA_TYPE_FILE, "File"),
    )

    post = models.ForeignKey(Post, related_name="media_items", on_delete=models.CASCADE)
    file = models.FileField(upload_to="posts/")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class Message(models.Model):
    nickname = models.CharField(max_length=32, blank=True)
    content = models.TextField()
    review_status = models.CharField(
        max_length=10,
        choices=(("approved", "Approved"), ("pending", "Pending"), ("rejected", "Rejected")),
        default="approved",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class BlockedKeyword(models.Model):
    keyword = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.keyword


class ContentReview(models.Model):
    REVIEW_TYPE_CHOICES = (
        ("comment", "Comment"),
        ("message", "Message"),
    )

    review_type = models.CharField(max_length=10, choices=REVIEW_TYPE_CHOICES)
    source_id = models.PositiveIntegerField()
    nickname = models.CharField(max_length=32, blank=True)
    content = models.TextField()
    ai_reason = models.CharField(max_length=200, blank=True)
    status = models.CharField(
        max_length=10,
        choices=(("pending", "待审核"), ("approved", "已通过"), ("rejected", "已拒绝")),
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["review_type", "source_id"]),
        ]


class SiteAnnouncement(models.Model):
    title = models.CharField(max_length=128)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class AnnouncementMedia(models.Model):
    MEDIA_TYPE_IMAGE = "image"
    MEDIA_TYPE_VIDEO = "video"
    MEDIA_TYPE_AUDIO = "audio"
    MEDIA_TYPE_FILE = "file"

    MEDIA_TYPE_CHOICES = (
        (MEDIA_TYPE_IMAGE, "Image"),
        (MEDIA_TYPE_VIDEO, "Video"),
        (MEDIA_TYPE_AUDIO, "Audio"),
        (MEDIA_TYPE_FILE, "File"),
    )

    announcement = models.ForeignKey(SiteAnnouncement, related_name="media_items", on_delete=models.CASCADE)
    file = models.FileField(upload_to="announcements/")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]



