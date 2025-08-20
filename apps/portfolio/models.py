from django.db import models
from PIL import Image as PilImage
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys


class Image(models.Model):
    file = models.ImageField(upload_to="project_images/")

    def save(self, *args, **kwargs):
        # Open the image using Pillow
        img = PilImage.open(self.file)
        # Convert to RGB mode if the image is in RGBA mode
        if img.mode == "RGBA":
            img = img.convert("RGB")
        # Compress the image
        output = BytesIO()
        img.save(output, format="JPEG", quality=70)
        output.seek(0)

        # Set the content of the compressed image to the file field
        self.file = InMemoryUploadedFile(
            output,
            "ImageField",
            f"{self.file.name.split('.')[0]}.jpg",
            "image/jpeg",
            sys.getsizeof(output),
            None,
        )

        super().save(*args, **kwargs)

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
