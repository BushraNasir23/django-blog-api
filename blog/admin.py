from django.contrib import admin
from .models import Post, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "is_private", "created_at"]
    list_filter = ["is_private", "created_at"]
    search_fields = ["title", "content", "author__username"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["post", "commenter", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["comment_text", "commenter__username", "post__title"]
