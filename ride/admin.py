from django.contrib import admin
from .models import Ride, RideBooking, Taxi, ServiceTaxi

# Register your models here.

admin.site.register(Ride)
admin.site.register(RideBooking)
admin.site.register(Taxi)
admin.site.register(ServiceTaxi)
