from django.db import models
from account.models import User
import uuid

# Create your models here.


class Posts(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    img = models.ImageField(null=True, default="/profile_icon.png")
    price = models.FloatField(blank=False, null=False, default=0.0)
    is_sold = models.BooleanField(blank=False, default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Name: {self.created_by.name} Title: {self.title} TimeStamp:{self.created_at}"


class Transactions(models.Model):
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, blank=False)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ID:{self.pk} TimeStamp:{self.created_at}"


class Item(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    barcode = models.CharField(max_length=100, unique=True)  # Primary barcode
    aliases = models.JSONField(
        default=list, blank=True
    )  # Store alternative barcodes as a list
    name = models.CharField(max_length=255)
    deals = models.JSONField(default=list)  # Store the list of deals as JSON

    def __str__(self):
        return self.name

class Inventory(models.Model):
    name = models.CharField(max_length=100, default="Tickets Inventory")  # Inventory name
    items = models.JSONField()  # Store the ticketsData JSON
    created_by = models.CharField(max_length=100)  # Just a string for the creator's name
    created_at = models.DateTimeField(auto_now_add=True)  # Auto-set on creation

    def __str__(self):
        return f"{self.name} created by {self.created_by}"