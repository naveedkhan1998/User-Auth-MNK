from django.db import models

# Create your models here.

class Student(models.Model):
    name = models.CharField(max_length=255,default='Naveed')
    standard = models.IntegerField(default=1)
    
    def __str__(self) -> str:
        return self.name