from django.urls import path,include
from .views import get_students_list,update_students_list




urlpatterns = [
        path('get_students/',get_students_list,name='get_students'),
        path('update_students/',update_students_list,name='update_students'),
]