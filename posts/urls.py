from django.urls import path, include
from .views import TransactionsList, ItemListCreateView, InventoryViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"inventories", InventoryViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("transactions/", TransactionsList.as_view(), name="transcations"),
    path("items/", ItemListCreateView.as_view(), name="item-list-create"),
    path("items/<str:pk>/", ItemListCreateView.as_view(), name="item-detail"),
]
