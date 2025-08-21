from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from .models import Message
from .serializers import MessageSerializer
from rest_framework import status


# Create your views here.
@permission_classes([AllowAny])
class MessageView(APIView):
    def get(self, request, format=None):
        data = Message.objects.all().order_by("-created_at")[:15]
        serializer = MessageSerializer(data, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {
                    "msg": "Message Sent",
                },
                status=status.HTTP_201_CREATED,
            )


class MessageList(APIView):
    def delete(self,request, pk):
        obj = Message.objects.filter(pk=pk)
        if not obj.exists():
            return Response({"error": "Not Found!"}, status=status.HTTP_404_NOT_FOUND)

        else:
            data = MessageSerializer(obj, many=False).data
            obj.delete()
            return Response(
                {"msg": "Success", "data": data}, status=status.HTTP_202_ACCEPTED
            )
