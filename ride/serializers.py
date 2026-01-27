from rest_framework import serializers
from django.conf import settings
from .models import Ride, RideBooking

User = settings.AUTH_USER_MODEL

class RideSerializer(serializers.ModelSerializer):
    driver_username = serializers.CharField(source='driver.username', read_only=True)
    bookings_count = serializers.IntegerField(
        source='bookings.count', read_only=True
    )
    drive_rating = serializers.FloatField(source='driver.rating', read_only=True)

    class Meta:
        model = Ride
        fields = [
            'id',
            'driver',
            'driver_username',
            'drive_rating',
            'from_city',
            'to_city',
            'departure_date',
            'departure_time',
            'price',
            'available_seats',
            'distance_km',
            'additional_info',
            'status',
            'created_at',
            'bookings_count',
        ]


class RideBookingSerializer(serializers.ModelSerializer):
    passenger_username = serializers.CharField(source='passenger.username', read_only=True)
    ride_details = RideSerializer(source='ride', read_only=True)

    class Meta:
        model = RideBooking
        fields = [
            'id',
            'ride',
            'ride_details',
            'passenger',
            'passenger_username',
            'status',
            'booked_at',
            'special_requests',
        ]

    def validate(self, data):
        ride = data.get('ride')
        if ride.bookings.count() >= ride.available_seats:
            raise serializers.ValidationError("No available seats for this ride.")
        return data
