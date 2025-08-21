from rest_framework import serializers
from .models import Posts, Transactions, Item, Inventory
from account.serializers import UserProfileSerializer


class PostsSerializer(serializers.ModelSerializer):
    created_by = UserProfileSerializer()

    class Meta:
        model = Posts
        fields = "__all__"


class TransactionsSerializer(serializers.ModelSerializer):
    post = PostsSerializer()
    buyer = UserProfileSerializer()

    class Meta:
        model = Transactions
        fields = "__all__"


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "barcode", "aliases", "name", "deals"]


class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ["id", "name", "items", "created_by", "created_at"]
        read_only_fields = ["id", "created_at"]
