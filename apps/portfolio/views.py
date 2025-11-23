# portfolio/views.py
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Project
from .serializers import ProjectSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def project_list(request):
    allowed_domains = ["https://mnaveedk.com", "https://www.mnaveedk.com"]

    if settings.DEBUG:
        allowed_domains.extend(
            [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:8000",
                "http://127.0.0.1:8000",
            ]
        )

    origin = request.META.get("HTTP_ORIGIN")

    # Allow if origin matches or if it's a direct browser request in DEBUG mode (no origin)
    if origin in allowed_domains or (settings.DEBUG and not origin):
        projects = Project.objects.all()
        serializer = ProjectSerializer(
            projects, many=True, context={"request": request}
        )
        return Response(serializer.data)

    return Response({"detail": "Unauthorized access"}, status=status.HTTP_403_FORBIDDEN)
