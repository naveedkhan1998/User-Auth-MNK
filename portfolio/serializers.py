# portfolio/serializers.py
from rest_framework import serializers
from .models import Project, Image

class ImageSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ['file_url']

    def get_file_url(self, obj):
        return self.context['request'].build_absolute_uri(obj.file.url)

class ProjectSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S.%fZ")

    class Meta:
        model = Project
        fields = ['id', 'images', 'created_at', 'title', 'description', 'technology_used', 'live_site_url', 'github_url']

    def get_images(self, obj):
        return [image['file_url'] for image in ImageSerializer(obj.images.all(), many=True, context=self.context).data]
