from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from .models import Posts, Transactions
from .serializers import PostsSerializer, TransactionsSerializer
from rest_framework import status

@permission_classes([AllowAny])
class PostsList(APIView):
    def get(self, requess):
        obj = Posts.objects.all()
        if not obj.exists():
            return Response({"error": "Not Found!"}, status=status.HTTP_404_NOT_FOUND)

        else:
            data = PostsSerializer(obj, many=True).data
            return Response(
                {"msg": "Success", "data": data}, status=status.HTTP_202_ACCEPTED
            )
        
@permission_classes([AllowAny])
class TransactionsList(APIView):
    def get(self, requess):
        obj = Transactions.objects.all()
        if not obj.exists():
            return Response({"error": "Not Found!"}, status=status.HTTP_404_NOT_FOUND)

        else:
            data = TransactionsSerializer(obj, many=True).data
            return Response(
                {"msg": "Success", "data": data}, status=status.HTTP_202_ACCEPTED
            )
