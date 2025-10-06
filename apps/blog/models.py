"""
Models for MDX blog post management.
"""
from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid


class BlogPost(models.Model):
    """
    Model representing an MDX blog post with metadata.
    The actual MDX content is stored as files (local or GCS).
    """
    
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(help_text="Short description/excerpt for the blog post")
    
    # Metadata
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="blog_posts"
    )
    tags = models.JSONField(default=list, blank=True, help_text="List of tags")
    
    # Featured image
    featured_image = models.ImageField(
        upload_to="blog/featured/", 
        null=True, 
        blank=True
    )
    featured_image_alt = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Alt text for featured image"
    )
    
    # Status and timestamps
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="draft"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # SEO fields
    meta_title = models.CharField(
        max_length=60, 
        blank=True,
        help_text="SEO meta title (leave blank to use post title)"
    )
    meta_description = models.CharField(
        max_length=160, 
        blank=True,
        help_text="SEO meta description"
    )
    
    # Reading time (auto-calculated)
    reading_time = models.IntegerField(
        default=0, 
        help_text="Estimated reading time in minutes"
    )
    
    # MDX file path (relative to storage backend)
    mdx_file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to the MDX file in storage"
    )
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status", "-published_at"]),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate slug from title if not provided
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Set mdx_file_path if not set
        if not self.mdx_file_path:
            self.mdx_file_path = f"blog/posts/{self.slug}.mdx"
        
        # Use meta_title as title if not provided
        if not self.meta_title:
            self.meta_title = self.title
        
        super().save(*args, **kwargs)
    
    def clean(self):
        # Validate slug uniqueness
        if self.slug:
            qs = BlogPost.objects.filter(slug=self.slug)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({"slug": "A blog post with this slug already exists."})


class BlogImage(models.Model):
    """
    Model for managing images associated with blog posts.
    Images can be referenced in MDX content.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blog_post = models.ForeignKey(
        BlogPost, 
        on_delete=models.CASCADE, 
        related_name="images"
    )
    image = models.ImageField(upload_to="blog/images/")
    alt_text = models.CharField(max_length=255, blank=True)
    caption = models.TextField(blank=True)
    
    # Image will be automatically deleted when BlogImage is deleted
    # thanks to django-cleanup if it's installed
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Blog Image"
        verbose_name_plural = "Blog Images"
    
    def __str__(self):
        return f"{self.blog_post.title} - {self.alt_text or self.image.name}"
