from django.db import models

# Create your models here.

class Message(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField( max_length=254) 
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)

    def __str__(self):
        return f'Name: {self.name} Message: {self.message[:20]}'
    