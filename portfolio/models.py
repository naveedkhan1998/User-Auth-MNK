# portfolio/models.py
from django.db import models


class Image(models.Model):
    file = models.ImageField(upload_to="project_images/")

    def __str__(self):
        return str(self.file)


class Project(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    technology_used = models.CharField(max_length=100)
    live_site_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    images = models.ManyToManyField(Image, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
