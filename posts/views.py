from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from .models import Posts, Transactions
from .serializers import PostsSerializer, TransactionsSerializer
from rest_framework import status
from .models import Item
from .serializers import ItemSerializer

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
@permission_classes([AllowAny])
class ItemListCreateView(APIView):
    def get(self, request, *args, **kwargs):
        items = Item.objects.all()
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = ItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)