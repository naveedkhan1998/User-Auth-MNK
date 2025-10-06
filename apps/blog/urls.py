"""
URL configuration for blog API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BlogPostViewSet, BlogImageViewSet

router = DefaultRouter()
router.register(r"posts", BlogPostViewSet, basename="blogpost")
router.register(r"images", BlogImageViewSet, basename="blogimage")

app_name = "blog"

urlpatterns = [
    path("", include(router.urls)),
]
