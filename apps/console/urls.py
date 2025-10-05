from django.urls import path

from .views import (
    ConsoleLoginView,
    ConsoleLogoutView,
    CreateDirectoryView,
    DeleteEntryView,
    DownloadFileView,
    FileManagerView,
    FileUploadView,
    MessageDetailView,
    MessageListView,
    ProjectCreateView,
    ProjectDeleteView,
    ProjectDetailView,
    ProjectImageDeleteView,
    ProjectImageUploadView,
    ProjectListView,
    ProjectUpdateView,
)


app_name = "console"

urlpatterns = [
    path("login/", ConsoleLoginView.as_view(), name="login"),
    path("logout/", ConsoleLogoutView.as_view(), name="logout"),
    path("", FileManagerView.as_view(), name="file-manager"),
    path("upload/", FileUploadView.as_view(), name="upload"),
    path("mkdir/", CreateDirectoryView.as_view(), name="mkdir"),
    path("delete/", DeleteEntryView.as_view(), name="delete"),
    path("download/", DownloadFileView.as_view(), name="download"),
    path("projects/", ProjectListView.as_view(), name="project-list"),
    path("projects/create/", ProjectCreateView.as_view(), name="project-create"),
    path("projects/<int:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    path("projects/<int:pk>/update/", ProjectUpdateView.as_view(), name="project-update"),
    path(
        "projects/<int:pk>/images/add/",
        ProjectImageUploadView.as_view(),
        name="project-image-add",
    ),
    path(
        "projects/<int:pk>/images/<int:image_pk>/delete/",
        ProjectImageDeleteView.as_view(),
        name="project-image-delete",
    ),
    path("projects/<int:pk>/delete/", ProjectDeleteView.as_view(), name="project-delete"),
    path("messages/", MessageListView.as_view(), name="message-list"),
    path("messages/<int:pk>/", MessageDetailView.as_view(), name="message-detail"),
]
