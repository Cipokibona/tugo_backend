from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Ride, RideBooking
from .serializers import RideSerializer, RideBookingSerializer

class RideViewSet(viewsets.ModelViewSet):
    queryset = Ride.objects.all().order_by('-departure_date', '-departure_time')
    serializer_class = RideSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Le driver = user connecté
        serializer.save(driver=self.request.user)


class RideBookingViewSet(viewsets.ModelViewSet):
    queryset = RideBooking.objects.all().order_by('-booked_at')
    serializer_class = RideBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        booking = serializer.save(passenger=self.request.user)
        ride = booking.ride
        # Mettre à jour le statut du ride si plus de places
        if ride.bookings.count() >= ride.available_seats:
            ride.status = 'FULL'
            ride.save()

