from rest_framework import serializers
from rest_framework.fields import IntegerField, CharField, DateTimeField
from .views import MessageView

class MessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = MessageView
        fields = '__all__'