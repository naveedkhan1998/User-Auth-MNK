from rest_framework import serializers
from rest_framework.fields import IntegerField, CharField, DateTimeField
from .models import Message

class MessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = '__all__'