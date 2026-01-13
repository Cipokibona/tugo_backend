from django.contrib import admin
from .models import User, UserSession, PageVisit, DriverProfile

# Register your models here.
admin.site.register(User)
admin.site.register(UserSession)
admin.site.register(PageVisit)
admin.site.register(DriverProfile)