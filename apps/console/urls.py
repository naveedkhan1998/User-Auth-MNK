from django.urls import path

from .views import (
    ConsoleLoginView,
    ConsoleLogoutView,
    CreateDirectoryView,
    DeleteEntryView,
    DownloadFileView,
    FileManagerView,
    FileUploadView,
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
]
