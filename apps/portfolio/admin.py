from django.contrib import admin
from django import forms
from .models import Project, Image


class ProjectAdminForm(forms.ModelForm):
    """Custom form for Project admin with multiple image upload capability"""

    class MultiFileInput(forms.ClearableFileInput):
        allow_multiple_selected = True

    additional_images = forms.FileField(
        required=False,
        widget=MultiFileInput(attrs={"multiple": True}),
        help_text="Upload multiple images at once. These will be added to the project's images.",
    )

    class Meta:
        model = Project
        fields = "__all__"

    def save(self, commit=True):
        instance = super().save(commit=False)

        if commit:
            instance.save()

        # Handle additional images upload
        if self.cleaned_data.get("additional_images"):
            files = self.files.getlist("additional_images")
            for uploaded_file in files:
                # Create Image instance for each uploaded file
                image_instance = Image(file=uploaded_file)
                image_instance.save()  # This will trigger the compression in the model's save method
                # Add to project's images
                instance.images.add(image_instance)

        return instance


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    form = ProjectAdminForm
    list_display = ("title", "technology_used", "created_at")
    search_fields = ("title", "description", "technology_used")
    filter_horizontal = ("images",)  # Allows easy selection of multiple images

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "description",
                    "technology_used",
                    "live_site_url",
                    "github_url",
                )
            },
        ),
        (
            "Images",
            {
                "fields": ("images", "additional_images"),
                "description": "Select existing images or upload new ones below.",
            },
        ),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    readonly_fields = ("created_at",)


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("file",)
