"""
API views for the blog app.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.db.models import Q

from .models import BlogPost, BlogImage
from .serializers import (
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    BlogPostCreateUpdateSerializer,
    BlogImageSerializer,
)


class BlogPostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for blog posts.

    List and retrieve are public.
    Create, update, delete require authentication and staff permission.
    """

    queryset = BlogPost.objects.all()
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "list":
            return BlogPostListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return BlogPostCreateUpdateSerializer
        return BlogPostDetailSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = BlogPost.objects.all()

        # Filter by status for non-staff users
        if not self.request.user.is_staff:
            queryset = queryset.filter(status="published")

        # Filter by tags
        tags = self.request.query_params.get("tags")
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            queryset = queryset.filter(tags__overlap=tag_list)

        # Search
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(tags__contains=[search])
            )

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter and self.request.user.is_staff:
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["post"])
    def publish(self, request, slug=None):
        """Publish a draft blog post."""
        if not request.user.is_staff:
            return Response(
                {"error": "Only staff can publish posts."},
                status=status.HTTP_403_FORBIDDEN,
            )

        blog_post = self.get_object()
        blog_post.status = "published"

        if not blog_post.published_at:
            from django.utils import timezone

            blog_post.published_at = timezone.now()

        blog_post.save()

        serializer = self.get_serializer(blog_post)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def unpublish(self, request, slug=None):
        """Unpublish a blog post."""
        if not request.user.is_staff:
            return Response(
                {"error": "Only staff can unpublish posts."},
                status=status.HTTP_403_FORBIDDEN,
            )

        blog_post = self.get_object()
        blog_post.status = "draft"
        blog_post.save()

        serializer = self.get_serializer(blog_post)
        return Response(serializer.data)


class BlogImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for blog images.

    Only authenticated staff users can manage images.
    """

    queryset = BlogImage.objects.all()
    serializer_class = BlogImageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = BlogImage.objects.all()

        # Filter by blog post
        blog_post_id = self.request.query_params.get("blog_post")
        if blog_post_id:
            queryset = queryset.filter(blog_post_id=blog_post_id)

        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        # Verify the blog post exists and user has permission
        blog_post = serializer.validated_data["blog_post"]
        if not self.request.user.is_staff:
            return Response(
                {"error": "Only staff can upload images."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer.save()
