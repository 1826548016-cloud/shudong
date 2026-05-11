from django.contrib import admin

from .models import Comment, Like, Post, SiteProfile


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
