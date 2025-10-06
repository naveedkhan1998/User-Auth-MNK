from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from .models import Message
from .serializers import MessageSerializer
from rest_framework import status


class MessagePostThrottle(AnonRateThrottle):
    """
    Custom throttle for anonymous message posting.
    Limits message submissions to prevent spam.
    """
    scope = 'message_post'


class MessageView(APIView):
    """
    Message endpoint with differentiated permissions:
    - POST: AllowAny (with rate limiting for anonymous users)
    - GET: IsAdminUser (staff only)
    """

    def get_permissions(self):
        """
        GET requests require admin/staff permissions.
        POST requests are open to anyone.
        """
        if self.request.method == 'GET':
            return [IsAdminUser()]
        return [AllowAny()]

    def get_throttles(self):
        """
        Apply rate limiting only to POST requests.
        """
        if self.request.method == 'POST':
            return [MessagePostThrottle()]
        return []

    def get(self, request, format=None):
        """List recent messages - Admin only"""
        data = Message.objects.all().order_by("-created_at")[:15]
        serializer = MessageSerializer(data, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        """Submit a message - Open to anyone (rate limited)"""
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
    """
    Delete individual messages - Admin only
    """
    permission_classes = [IsAdminUser]

    def delete(self, request, pk):
        """Delete a specific message by ID"""
        obj = Message.objects.filter(pk=pk)
        if not obj.exists():
            return Response({"error": "Not Found!"}, status=status.HTTP_404_NOT_FOUND)

        data = MessageSerializer(obj.first(), many=False).data
        obj.delete()
        return Response(
            {"msg": "Success", "data": data}, status=status.HTTP_202_ACCEPTED
        )
