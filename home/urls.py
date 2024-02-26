# urls.py
from django.urls import path
from .views import StaticFilesListView, serve_static

urlpatterns = [
    path("static/", StaticFilesListView.as_view(), name="static-files-list"),
    path("static/<path:path>", serve_static, name="serve-static"),
    # Your other URL patterns
]
