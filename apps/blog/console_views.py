"""
Console views for the blog CMS.
Staff-only views for managing blog posts.
"""

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views import View

from .models import BlogPost, BlogImage
from .forms import BlogPostForm, BlogImageForm


class StaffOnlyMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to ensure only staff users can access console views."""

    login_url = reverse_lazy("console:login")

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(
                self.request, "You do not have permission to access the blog console."
            )
            return redirect("console:login")
        return super().handle_no_permission()


class BlogPostListView(StaffOnlyMixin, ListView):
    """List all blog posts in the console."""

    model = BlogPost
    template_name = "console/blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 20

    def get_queryset(self):
        queryset = BlogPost.objects.all().select_related("author")

        # Filter by status
        status_filter = self.request.GET.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Search
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(title__icontains=search)

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_filter"] = self.request.GET.get("status", "")
        context["search"] = self.request.GET.get("search", "")
        return context


class BlogPostCreateView(StaffOnlyMixin, CreateView):
    """Create a new blog post."""

    model = BlogPost
    form_class = BlogPostForm
    template_name = "console/blog/post_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request, f"Blog post '{form.instance.title}' created successfully!"
        )
        return response

    def get_success_url(self):
        return reverse("console:blog-post-update", kwargs={"pk": self.object.pk})


class BlogPostUpdateView(StaffOnlyMixin, UpdateView):
    """Update an existing blog post."""

    model = BlogPost
    form_class = BlogPostForm
    template_name = "console/blog/post_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, f"Blog post '{form.instance.title}' updated successfully!"
        )
        return response

    def get_success_url(self):
        return reverse("console:blog-post-update", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["images"] = self.object.images.all()
        return context


class BlogPostDeleteView(StaffOnlyMixin, DeleteView):
    """Delete a blog post."""

    model = BlogPost
    template_name = "console/blog/post_confirm_delete.html"
    success_url = reverse_lazy("console:blog-post-list")

    def delete(self, request, *args, **kwargs):
        blog_post = self.get_object()

        # Delete MDX file from storage
        if blog_post.mdx_file_path:
            try:
                from .storage_backends import get_mdx_storage_backend

                storage = get_mdx_storage_backend()
                if storage.exists(blog_post.mdx_file_path):
                    storage.delete(blog_post.mdx_file_path)
            except Exception as e:
                messages.warning(request, f"Failed to delete MDX file: {e}")

        messages.success(
            request, f"Blog post '{blog_post.title}' deleted successfully!"
        )
        return super().delete(request, *args, **kwargs)


class BlogImageUploadView(StaffOnlyMixin, CreateView):
    """Upload an image for a blog post."""

    model = BlogImage
    form_class = BlogImageForm
    template_name = "console/blog/image_upload.html"

    def dispatch(self, request, *args, **kwargs):
        self.blog_post = get_object_or_404(BlogPost, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.blog_post = self.blog_post
        response = super().form_valid(form)
        messages.success(self.request, "Image uploaded successfully!")
        return response

    def get_success_url(self):
        return reverse("console:blog-post-update", kwargs={"pk": self.blog_post.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["blog_post"] = self.blog_post
        return context


class BlogImageDeleteView(StaffOnlyMixin, DeleteView):
    """Delete a blog image."""

    model = BlogImage
    template_name = "console/blog/image_confirm_delete.html"

    def dispatch(self, request, *args, **kwargs):
        self.blog_post = get_object_or_404(BlogPost, pk=kwargs["post_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(
            BlogImage, pk=self.kwargs["image_pk"], blog_post=self.blog_post
        )

    def delete(self, request, *args, **kwargs):
        image = self.get_object()
        messages.success(request, "Image deleted successfully!")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("console:blog-post-update", kwargs={"pk": self.blog_post.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["blog_post"] = self.blog_post
        return context


class BlogImageUploadAPIView(StaffOnlyMixin, View):
    """
    JSON API endpoint for uploading images via drag-and-drop or paste.
    Used by the markdown editor for inline image uploads.
    """

    def post(self, request, pk):
        """Handle image upload and return JSON response."""
        blog_post = get_object_or_404(BlogPost, pk=pk)

        # Check if image file is present
        if "image" not in request.FILES:
            return JsonResponse({"error": "No image file provided"}, status=400)

        image_file = request.FILES["image"]
        alt_text = request.POST.get("alt_text", "")
        caption = request.POST.get("caption", "")

        # Validate file type
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
        if image_file.content_type not in allowed_types:
            return JsonResponse(
                {"error": f"Invalid file type. Allowed types: {', '.join(allowed_types)}"},
                status=400,
            )

        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if image_file.size > max_size:
            return JsonResponse(
                {"error": "File size exceeds 5MB limit"}, status=400
            )

        try:
            # Create BlogImage instance
            blog_image = BlogImage.objects.create(
                blog_post=blog_post,
                image=image_file,
                alt_text=alt_text or image_file.name,
                caption=caption,
            )

            # Return success response with image URL
            return JsonResponse(
                {
                    "success": True,
                    "alt_text": blog_image.alt_text,
                    "image_url": blog_image.image.url,
                    "caption": blog_image.caption,
                },
                status=201,
            )

        except Exception as e:
            return JsonResponse(
                {"error": f"Failed to upload image: {str(e)}"}, status=500
            )
