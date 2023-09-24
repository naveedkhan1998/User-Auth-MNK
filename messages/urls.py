from django.urls import path,include
from .views import MessageView




urlpatterns = [
    path('',MessageView.as_view(),name='message'),

]