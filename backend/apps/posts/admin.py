from django.contrib import admin

from .models import AnnouncementMedia, Comment, ContentReview, Like, Post, SiteAnnouncement, SiteProfile


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "media_type", "view_count", "like_count")
    search_fields = ("content",)
    list_filter = ("media_type", "created_at")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post_id", "nickname", "created_at", "ip_address")
    search_fields = ("nickname", "content")
    list_filter = ("created_at",)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("id", "post_id", "ip_address", "created_at")
    list_filter = ("created_at",)


@admin.register(SiteProfile)
class SiteProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "nickname", "updated_at")


@admin.register(SiteAnnouncement)
class SiteAnnouncementAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "content")


@admin.register(ContentReview)
class ContentReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "review_type", "source_id", "nickname", "status", "created_at")
    list_filter = ("status", "review_type")
    search_fields = ("nickname", "content")
