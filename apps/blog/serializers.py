"""
Serializers for the blog app.
"""
from rest_framework import serializers
from .models import BlogPost, BlogImage
from django.utils import timezone


class BlogImageSerializer(serializers.ModelSerializer):
    """Serializer for blog images."""
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogImage
        fields = [
            "id",
            "blog_post",
            "image",
            "image_url",
            "alt_text",
            "caption",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "image_url"]
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class BlogPostListSerializer(serializers.ModelSerializer):
    """Serializer for listing blog posts (without full MDX content)."""
    
    author_name = serializers.CharField(source="author.name", read_only=True)
    featured_image_url = serializers.SerializerMethodField()
    image_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "author",
            "author_name",
            "tags",
            "featured_image",
            "featured_image_url",
            "featured_image_alt",
            "status",
            "created_at",
            "updated_at",
            "published_at",
            "reading_time",
            "image_count",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def get_featured_image_url(self, obj):
        if obj.featured_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image.url)
            return obj.featured_image.url
        return None
    
    def get_image_count(self, obj):
        return obj.images.count()


class BlogPostDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed blog post view with MDX content."""
    
    author_name = serializers.CharField(source="author.name", read_only=True)
    featured_image_url = serializers.SerializerMethodField()
    images = BlogImageSerializer(many=True, read_only=True)
    mdx_content = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "author",
            "author_name",
            "tags",
            "featured_image",
            "featured_image_url",
            "featured_image_alt",
            "status",
            "created_at",
            "updated_at",
            "published_at",
            "meta_title",
            "meta_description",
            "reading_time",
            "mdx_file_path",
            "mdx_content",
            "images",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "mdx_content"]
    
    def get_featured_image_url(self, obj):
        if obj.featured_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image.url)
            return obj.featured_image.url
        return None
    
    def get_mdx_content(self, obj):
        """Retrieve MDX content from storage backend."""
        if not obj.mdx_file_path:
            return None
        
        try:
            from .storage_backends import get_mdx_storage_backend
            storage = get_mdx_storage_backend()
            
            if storage.exists(obj.mdx_file_path):
                mdx_file = storage.read_mdx_file(obj.mdx_file_path)
                return mdx_file.raw_content
        except Exception as e:
            # Log the error but don't fail the serialization
            print(f"Error reading MDX file for {obj.slug}: {e}")
        
        return None


class BlogPostCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating blog posts."""
    
    mdx_content = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Full MDX content including frontmatter"
    )
    
    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "author",
            "tags",
            "featured_image",
            "featured_image_alt",
            "status",
            "published_at",
            "meta_title",
            "meta_description",
            "reading_time",
            "mdx_content",
        ]
        read_only_fields = ["id"]
    
    def validate_slug(self, value):
        """Ensure slug is unique."""
        if value:
            qs = BlogPost.objects.filter(slug=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "A blog post with this slug already exists."
                )
        return value
    
    def create(self, validated_data):
        mdx_content = validated_data.pop('mdx_content', '')
        
        # Auto-set published_at if status is published and not set
        if validated_data.get('status') == 'published' and not validated_data.get('published_at'):
            validated_data['published_at'] = timezone.now()
        
        blog_post = BlogPost.objects.create(**validated_data)
        
        # Save MDX content to storage if provided
        if mdx_content:
            self._save_mdx_content(blog_post, mdx_content)
        
        return blog_post
    
    def update(self, instance, validated_data):
        mdx_content = validated_data.pop('mdx_content', None)
        
        # Update published_at if status changed to published
        if validated_data.get('status') == 'published' and instance.status != 'published':
            if not validated_data.get('published_at'):
                validated_data['published_at'] = timezone.now()
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update MDX content if provided
        if mdx_content is not None:
            self._save_mdx_content(instance, mdx_content)
        
        return instance
    
    def _save_mdx_content(self, blog_post, mdx_content):
        """Save MDX content to storage backend."""
        from .storage_backends import get_mdx_storage_backend, MDXStorageMixin
        
        storage = get_mdx_storage_backend()
        
        # Parse existing content or use provided
        metadata_dict, content = MDXStorageMixin.parse_mdx(mdx_content)
        
        # Update metadata with blog post fields
        metadata = {
            "title": blog_post.title,
            "description": blog_post.description,
            "tags": blog_post.tags,
            "author": blog_post.author.name if blog_post.author else "",
            "published_at": blog_post.published_at.isoformat() if blog_post.published_at else "",
            "reading_time": blog_post.reading_time,
        }
        
        # Merge with any custom metadata from the MDX file
        metadata.update(metadata_dict)
        
        # Write to storage
        storage.write_mdx_file(blog_post.mdx_file_path, metadata, content)
