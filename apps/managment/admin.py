from django.contrib import admin
from .models import Student,Standard,Subject,ClassRoom,ClassRoomAttendance
# Register your models here.
admin.site.register(Standard)
admin.site.register(Subject)
admin.site.register(Student)
admin.site.register(ClassRoom)
admin.site.register(ClassRoomAttendance)