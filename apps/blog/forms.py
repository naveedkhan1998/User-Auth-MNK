"""
Forms for the blog CMS in the console.
"""
from django import forms
from .models import BlogPost, BlogImage


class BlogPostForm(forms.ModelForm):
    """Form for creating and editing blog posts."""
    
    mdx_content = forms.CharField(
        widget=forms.Textarea(attrs={
            "rows": 20,
            "class": "w-full font-mono text-sm",
            "placeholder": "Write your MDX content here..."
        }),
        required=False,
        help_text="Write your blog post content in MDX format"
    )
    
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "Enter tags separated by commas"
        }),
        help_text="Separate tags with commas"
    )
    
    class Meta:
        model = BlogPost
        fields = [
            "title",
            "slug",
            "description",
            "tags_input",
            "featured_image",
            "featured_image_alt",
            "status",
            "published_at",
            "meta_title",
            "meta_description",
            "mdx_content",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "published_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "meta_description": forms.Textarea(attrs={"rows": 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Load existing MDX content if editing
        if self.instance and self.instance.pk and self.instance.mdx_file_path:
            try:
                from .storage_backends import get_mdx_storage_backend
                storage = get_mdx_storage_backend()
                
                if storage.exists(self.instance.mdx_file_path):
                    mdx_file = storage.read_mdx_file(self.instance.mdx_file_path)
                    self.initial["mdx_content"] = mdx_file.raw_content
            except Exception as e:
                print(f"Error loading MDX content: {e}")
        
        # Convert tags list to comma-separated string
        if self.instance and self.instance.pk and self.instance.tags:
            self.initial["tags_input"] = ", ".join(self.instance.tags)
        
        # Add CSS classes to all fields
        base_classes = (
            "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 "
            "text-sm transition focus:outline-none focus:ring-2 focus:ring-blue-500 "
            "dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
        )
        
        for field_name, field in self.fields.items():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {base_classes}".strip()
    
    def clean_tags_input(self):
        """Convert comma-separated tags to list."""
        tags_input = self.cleaned_data.get("tags_input", "")
        if tags_input:
            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
            return tags
        return []
    
    def clean_slug(self):
        """Ensure slug is unique."""
        slug = self.cleaned_data.get("slug")
        if slug:
            qs = BlogPost.objects.filter(slug=slug)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("A blog post with this slug already exists.")
        return slug
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set tags from tags_input
        instance.tags = self.cleaned_data.get("tags_input", [])
        
        if commit:
            instance.save()
            
            # Save MDX content to storage
            mdx_content = self.cleaned_data.get("mdx_content", "")
            if mdx_content:
                self._save_mdx_content(instance, mdx_content)
        
        return instance
    
    def _save_mdx_content(self, blog_post, mdx_content):
        """Save MDX content to storage backend."""
        from .storage_backends import get_mdx_storage_backend, MDXStorageMixin
        
        storage = get_mdx_storage_backend()
        
        # Parse content
        metadata_dict, content = MDXStorageMixin.parse_mdx(mdx_content)
        
        # Update metadata with blog post fields
        metadata = {
            "title": blog_post.title,
            "description": blog_post.description,
            "tags": blog_post.tags,
            "author": blog_post.author.name if blog_post.author else "",
            "published_at": blog_post.published_at.isoformat() if blog_post.published_at else "",
        }
        
        # Calculate reading time
        reading_time = MDXStorageMixin.calculate_reading_time(content)
        metadata["reading_time"] = reading_time
        blog_post.reading_time = reading_time
        blog_post.save(update_fields=["reading_time"])
        
        # Merge with any custom metadata
        metadata.update(metadata_dict)
        
        # Write to storage
        storage.write_mdx_file(blog_post.mdx_file_path, metadata, content)


class BlogImageForm(forms.ModelForm):
    """Form for uploading blog images."""
    
    class Meta:
        model = BlogImage
        fields = ["image", "alt_text", "caption"]
        widgets = {
            "caption": forms.Textarea(attrs={"rows": 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes
        base_classes = (
            "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 "
            "text-sm transition focus:outline-none focus:ring-2 focus:ring-blue-500"
        )
        
        for field_name, field in self.fields.items():
            if field_name != "image":
                existing = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = f"{existing} {base_classes}".strip()
