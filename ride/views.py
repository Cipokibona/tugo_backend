from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Ride, RideBooking
from .serializers import RideSerializer, RideBookingSerializer
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime


class RideViewSet(viewsets.ModelViewSet):
    queryset = Ride.objects.all().order_by('-departure_date', '-departure_time')
    serializer_class = RideSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        now = timezone.now()

        # Build current date and time
        today = now.date()
        current_time = now.time()

        # Past rides (past date OR today with past time)
        past_rides = Ride.objects.filter(
            Q(departure_date__lt=today)
            | Q(departure_date=today, departure_time__lt=current_time),
            status__in=['PENDING', 'OPEN']
        ).annotate(
            booking_count=Count('bookings')
        ).filter(
            booking_count=0
        )

        # Mark as CANCELLED when no bookings
        past_rides.update(status='CANCELLED')

        return Ride.objects.all().order_by('-departure_date', '-departure_time')

    def perform_create(self, serializer):
        serializer.save(driver=self.request.user)


class RideBookingViewSet(viewsets.ModelViewSet):
    queryset = RideBooking.objects.all().order_by('-booked_at')
    serializer_class = RideBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        today = timezone.localdate()
        RideBooking.objects.filter(
            ride__departure_date__lt=today
        ).exclude(
            status__in=['CANCELLED', 'CLOSED']
        ).update(status='CLOSED')
        return super().get_queryset()

    def _sync_ride_status(self, ride):
        active_bookings = ride.bookings.exclude(status__in=['CANCELLED', 'CLOSED']).count()
        target_status = 'FULL' if active_bookings >= ride.available_seats else 'OPEN'

        if ride.status != target_status:
            ride.status = target_status
            ride.save(update_fields=['status'])

    def perform_create(self, serializer):
        booking = serializer.save(passenger=self.request.user)
        self._sync_ride_status(booking.ride)

    def perform_update(self, serializer):
        previous_ride = serializer.instance.ride
        booking = serializer.save()

        self._sync_ride_status(booking.ride)
        if previous_ride != booking.ride:
            self._sync_ride_status(previous_ride)

    def perform_destroy(self, instance):
        ride = instance.ride
        instance.delete()
        self._sync_ride_status(ride)
