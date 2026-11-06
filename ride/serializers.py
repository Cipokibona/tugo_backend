from rest_framework import serializers
from django.db import transaction
from django.conf import settings
from django.conf import settings
from .models import GameScore, Ride, RideBooking, Taxi, ServiceTaxi
# from django.contrib.gis.geos import LineString

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
            'share_code',
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
            'route_coords',
            'additional_info',
            'status',
            # 'route',
            'proposer',
            'vehicule',
            'note',
            'created_at',
            'bookings_count',
        ]
        read_only_fields = [
            'share_code',
            'driver',
            'driver_username',
            'drive_rating',
            'created_at',
            'bookings_count',
        ]

    # def create(self, validated_data):
    #     coords = validated_data.pop('route_coords', None)  # Liste [[lng, lat], [lng, lat]]
    #     ride = Ride.objects.create(**validated_data)
    #     if coords:
    #         ride.route = LineString(coords)  # GeoDjango LineString
    #         ride.save()
    #     return ride


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
            'updated_at',
            'special_requests',
            'payment_method',
        ]
        read_only_fields = ['passenger']

    @transaction.atomic
    def create(self, validated_data):
        payment_method = validated_data.pop('payment_method', 'AFRIPAY').upper()
        passenger = self.context['request'].user
        ride = validated_data['ride']
        if payment_method == 'TUGO_MONEY':
            from decimal import Decimal
            from wallet.services import debit
            base = Decimal(str(ride.price))
            commission = base * Decimal(str(getattr(settings, 'RIDE_PLATFORM_COMMISSION_RATE', '0.10')))
            total = (base + commission + commission * Decimal('0.18')).quantize(Decimal('0.01'))
            debit(passenger, total, 'RIDE_PAYMENT', 'RIDE', f'Payment for ride {ride.pk}')
            validated_data['status'] = 'CONFIRMED'
        elif payment_method != 'AFRIPAY':
            raise serializers.ValidationError({'payment_method': 'Unsupported payment method.'})
        validated_data['payment_method'] = payment_method
        return super().create(validated_data)

    def validate(self, data):
        # For updates, only validate seat availability if `ride` is explicitly changed.
        if self.instance is not None and 'ride' not in data:
            return data

        ride = data.get('ride')
        if ride is None:
            return data

        # Proposed rides are requests and should stay joinable by clients.
        if ride.status == 'PROPOSED':
            return data

        bookings_qs = ride.bookings.exclude(status__in=['CANCELLED', 'CLOSED'])
        if self.instance is not None:
            bookings_qs = bookings_qs.exclude(pk=self.instance.pk)

        if bookings_qs.count() >= ride.available_seats:
            raise serializers.ValidationError("No available seats for this ride.")
        return data


class TaxiSerializer(serializers.ModelSerializer):
    driver_username = serializers.CharField(source='driver.username', read_only=True)

    class Meta:
        model = Taxi
        fields = [
            'id',
            'driver',
            'driver_username',
            'license_plate_number',
            'vehicle_model',
            'number_of_seats',
            'image',
            'color',
            'vehicle_year',
            'additional_details',
            'latitude',
            'longitude',
            'location_label',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'driver',
            'driver_username',
            'created_at',
            'updated_at',
        ]


class ServiceTaxiSerializer(serializers.ModelSerializer):
    client_username = serializers.CharField(source='client.username', read_only=True)
    taxi_details = TaxiSerializer(source='taxi', read_only=True)
    driver = serializers.IntegerField(source='taxi.driver.id', read_only=True)
    driver_username = serializers.CharField(source='taxi.driver.username', read_only=True)

    class Meta:
        model = ServiceTaxi
        fields = [
            'id',
            'taxi',
            'taxi_details',
            'driver',
            'driver_username',
            'client',
            'client_username',
            'pickup_location',
            'dropoff_location',
            'pickup_date',
            'pickup_time',
            'price',
            'distance_km',
            'status',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'client',
            'client_username',
            'created_at',
            'updated_at',
        ]


class GameScoreSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)

    class Meta:
        model = GameScore
        fields = [
            'id',
            'player',
            'player_username',
            'mode',
            'score',
            'distance',
            'remaining_time',
            'money_delta',
            'max_combo',
            'outcome',
            'payload',
            'created_at',
        ]
        read_only_fields = [
            'player',
            'player_username',
            'created_at',
        ]
