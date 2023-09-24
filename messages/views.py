from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from .serializers import MessageSerializer
from rest_framework import status


# Create your views here.
@permission_classes([AllowAny])
class MessageView(APIView):
    def post(self, request, format=None):
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            obj = serializer.save()
            return Response(
                {
                    "new_object": {"id": obj.id, **serializer.data},
                    "msg": "created_succesfully",
                },
                status=status.HTTP_201_CREATED,
            )
