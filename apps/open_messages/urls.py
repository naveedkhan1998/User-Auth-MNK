from django.urls import path
from .views import MessageView, MessageList


urlpatterns = [
    path("", MessageView.as_view(), name="message"),
    path("<int:pk>", MessageList.as_view(), name="message_delete"),
]
