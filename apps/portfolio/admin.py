from django.contrib import admin
from .models import Project, Image


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'technology_used', 'created_at')
    search_fields = ('title', 'description', 'technology_used')
    filter_horizontal = ('images',)  # Allows easy selection of multiple images


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('file',)
