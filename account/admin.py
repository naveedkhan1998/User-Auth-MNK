from django.contrib import admin
from account.models import User, UserOtps
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register your models here.


admin.site.register(User)
admin.site.register(UserOtps)
