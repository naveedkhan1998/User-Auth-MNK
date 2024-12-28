from django.contrib import admin
from .models import Posts, Transactions, Item, Inventory

# Register your models here.
admin.site.register(Posts)
admin.site.register(Transactions)
admin.site.register(Item)
admin.site.register(Inventory)
