from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.conf import settings
from drf_spectacular.renderers import OpenApiYamlRenderer
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.permissions import IsAdminUser

class SpectacularYAMLView(SpectacularAPIView):
    renderer_classes = [OpenApiYamlRenderer]


urlpatterns = (
    [
        path("admin/", admin.site.urls),
        path("api/user/", include("apps.account.urls")),
        path("api/message/", include("apps.open_messages.urls")),
        path("management/", include("apps.managment.urls")),
        path("posts/", include("apps.posts.urls")),
        path("portfolio/", include("apps.portfolio.urls")),
        path("home/", include("apps.home.urls")),
        path("console/", include("apps.console.urls")),
        path("api/schema/", SpectacularAPIView.as_view(permission_classes=[IsAdminUser]), name="schema"),
        path("api/schema.yaml", SpectacularYAMLView.as_view(permission_classes=[IsAdminUser]), name="schema-yaml"),
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[IsAdminUser]), name="swagger-ui"),
        path("api/redoc/", SpectacularRedocView.as_view(url_name="schema", permission_classes=[IsAdminUser]), name="redoc"),
        path("", TemplateView.as_view(template_name="index.html"), name="landing"),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.OUTPUT_URL, document_root=settings.OUTPUT_ROOT)
)
