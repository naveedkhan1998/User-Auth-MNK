from rest_framework import serializers
from .models import Posts,Transactions
from account.serializers import UserProfileSerializer

class PostsSerializer(serializers.ModelSerializer):
    created_by = UserProfileSerializer()
    class Meta:
        model = Posts
        fields = "__all__"

        
class TransactionsSerializer(serializers.ModelSerializer):
    posts = PostsSerializer()
    buyer = UserProfileSerializer()
    class Meta:
        model = Transactions
        fields = "__all__"
