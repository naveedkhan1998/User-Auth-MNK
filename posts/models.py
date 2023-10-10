from django.db import models
from account.models import User

# Create your models here.


class Posts(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,blank=False)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    img = models.ImageField(null=True, default="/profile_icon.png")
    price = models.FloatField(blank=False,null=False,default=0.0)
    is_sold = models.BooleanField(blank=False,default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Name: {self.created_by.name} Title: {self.title} TimeStamp:{self.created_at}"
    
class Transactions(models.Model):
    post = models.ForeignKey(Posts,on_delete=models.CASCADE,blank=False)
    buyer = models.ForeignKey(User,on_delete=models.CASCADE,blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ID:{self.pk} TimeStamp:{self.created_at}"
