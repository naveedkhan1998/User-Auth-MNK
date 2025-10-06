from django.contrib import admin
from .models import BlogPost, BlogImage


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "status", "author", "created_at", "published_at"]
    list_filter = ["status", "created_at", "published_at"]
    search_fields = ["title", "description", "slug"]
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "created_at"
    readonly_fields = ["created_at", "updated_at"]


@admin.register(BlogImage)
class BlogImageAdmin(admin.ModelAdmin):
    list_display = ["blog_post", "alt_text", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["blog_post__title", "alt_text", "caption"]
