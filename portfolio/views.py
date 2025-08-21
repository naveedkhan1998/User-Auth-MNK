# portfolio/views.py
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import render
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Project
from .serializers import ProjectSerializer
from backend.settings import BASE_DIR


@api_view(["GET"])
@permission_classes([AllowAny])
def project_list(request):
    allowed_domain = "https://mnaveedk.com"
    # if request.META.get("HTTP_ORIGIN") == allowed_domain:
    projects = Project.objects.all()
    serializer = ProjectSerializer(projects, many=True, context={"request": request})
    return Response(serializer.data)
    # else:
    # error_message = "Unauthorized access"
    # path_to_html = str(BASE_DIR) + "/home/templates/email_otp.html"
    # return render(request, 'error_template.html', {'error_message': error_message}, status=403)
