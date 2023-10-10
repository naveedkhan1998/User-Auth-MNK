from django.urls import path,include
from .views import PostsList,TransactionsList




urlpatterns = [
    path('',PostsList.as_view(),name='posts'),
    path('/transactions',TransactionsList.as_view(),name='transcations'),

]