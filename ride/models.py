from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

# Create your models here.
class Ride(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('FULL', 'Full'),
        ('CANCELLED', 'Cancelled'),
    )

    driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='rides_created'
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
        max_length=10,
        choices=STATUS_CHOICES,
        default='OPEN'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_city} → {self.to_city} ({self.departure_date})"
    
# rides/models.py
class RideBooking(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    )

    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='bookings')
    passenger = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    booked_at = models.DateTimeField(auto_now_add=True)
    special_requests = models.TextField(null=True, blank=True)