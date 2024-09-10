from django.urls import path, include
from .views import PostsList, TransactionsList, ItemListCreateView


urlpatterns = [
    path("", PostsList.as_view(), name="posts"),
    path("transactions/", TransactionsList.as_view(), name="transcations"),
    path("items/", ItemListCreateView.as_view(), name="item-list-create"),
    path('items/<str:pk>/', ItemListCreateView.as_view(), name='item-detail'),
]
