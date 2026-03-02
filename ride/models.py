from django.db import models
from django.conf import settings
# from django.contrib.gis.db import models as geomodels

User = settings.AUTH_USER_MODEL

# Create your models here.
class Ride(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('FULL', 'Full'),
        ('COMPLETED', 'Completed'),
        ('IN_PROGRESS', 'In Progress'),
        ('PROPOSED', 'Proposed'),
        ('CANCELLED', 'Cancelled'),
    )

    driver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rides_created'
    )

    proposer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rides_proposed'
    )

    # Route
    from_city = models.CharField(max_length=100)
    to_city = models.CharField(max_length=100)

    # Date & time
    departure_date = models.DateField()
    departure_time = models.TimeField()

    # Price
    price = models.PositiveIntegerField(help_text="Price in BIF")

    # Seats
    available_seats = models.PositiveSmallIntegerField(default=1)

    distance_km = models.PositiveIntegerField(null=True, blank=True)

    additional_info = models.TextField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OPEN'
    )

    # route = geomodels.LineStringField(null=True, blank=True, srid=4326)

    vehicule = models.TextField(null=True, blank=True)

    note = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_city} → {self.to_city} ({self.departure_date})"
    
# rides/models.py
class RideBooking(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('CLOSED', 'Closed'),
    )

    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='bookings')
    passenger = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    booked_at = models.DateTimeField(auto_now_add=True)
    special_requests = models.TextField(null=True, blank=True)


class Taxi(models.Model):
    driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='taxis'
    )
    license_plate_number = models.CharField(max_length=50, unique=True)
    vehicle_model = models.CharField(max_length=120)
    number_of_seats = models.PositiveSmallIntegerField(default=4)
    image = models.URLField(max_length=500, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    vehicle_year = models.PositiveSmallIntegerField(null=True, blank=True)
    additional_details = models.TextField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_label = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.license_plate_number} - {self.vehicle_model}"


class ServiceTaxi(models.Model):
    STATUS_CHOICES = (
        ('REQUESTED', 'Requested'),
        ('ACCEPTED', 'Accepted'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    taxi = models.ForeignKey(
        Taxi,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='services'
    )
    client = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taxi_services_as_client'
    )
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    pickup_date = models.DateField(null=True, blank=True)
    pickup_time = models.TimeField(null=True, blank=True)
    price = models.PositiveIntegerField(null=True, blank=True, help_text="Price in BIF")
    distance_km = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"Taxi service {self.id} - "
            f"{self.pickup_location} to {self.dropoff_location} ({self.status})"
        )
