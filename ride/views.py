from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Ride, RideBooking
from .serializers import RideSerializer, RideBookingSerializer
from notification.models import Notification
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta


class RideViewSet(viewsets.ModelViewSet):
    queryset = Ride.objects.all().order_by('-departure_date', '-departure_time')
    serializer_class = RideSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        now = timezone.localtime()
        closed_cutoff = now - timedelta(hours=1)

        # Close rides 1 hour after departure, but only when current status is OPEN.
        Ride.objects.filter(
            Q(departure_date__lt=closed_cutoff.date())
            | Q(
                departure_date=closed_cutoff.date(),
                departure_time__lte=closed_cutoff.time()
            ),
            status='OPEN'
        ).update(status='CLOSED')

        return Ride.objects.all().order_by('-departure_date', '-departure_time')

    def perform_create(self, serializer):
        status = serializer.validated_data.get('status', 'OPEN')

        if status == 'PROPOSED':
            serializer.save(proposer=self.request.user, driver=None)
        else:
            serializer.save(driver=self.request.user, proposer=None)


class RideBookingViewSet(viewsets.ModelViewSet):
    queryset = RideBooking.objects.all().order_by('-booked_at')
    serializer_class = RideBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _sync_ride_status(self, ride):
        if ride.status in ['CANCELLED', 'COMPLETED', 'CLOSED', 'PROPOSED']:
            return

        active_bookings = ride.bookings.exclude(status__in=['CANCELLED', 'CLOSED']).count()
        target_status = 'FULL' if active_bookings >= ride.available_seats else 'OPEN'

        if ride.status != target_status:
            ride.status = target_status
            ride.save(update_fields=['status'])

    def perform_create(self, serializer):
        booking = serializer.save(passenger=self.request.user)
        ride_owner = booking.ride.driver or booking.ride.proposer
        if ride_owner and ride_owner != self.request.user:
            Notification.objects.create(
                recipient=ride_owner,
                sender=self.request.user,
                title='New booking request',
                message=(
                    f"{self.request.user.username} joined your ride "
                    f"from {booking.ride.from_city} to {booking.ride.to_city}."
                ),
                notification_type='BOOKING_CREATED',
            )
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
