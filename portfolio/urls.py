# portfolio/urls.py
from django.urls import path
from .views import project_list

urlpatterns = [
    path("projects/", project_list, name="project-list"),
    # Add more paths as needed
]
