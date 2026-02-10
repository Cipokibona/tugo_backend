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

        # Construire date+heure actuelle
        today = now.date()
        current_time = now.time()

        # Rides déjà passés (date passée OU aujourd’hui avec heure passée)
        past_rides = Ride.objects.filter(
            Q(departure_date__lt=today) |
            Q(departure_date=today, departure_time__lt=current_time),
            status__in=['PENDING', 'OPEN']  # adapte selon tes statuts
        ).annotate(
            booking_count=Count('bookings')
        ).filter(
            booking_count=0
        )

        # Mettre à jour en CANCELLED si aucun booking
        past_rides.update(status='CANCELLED')

        # Queryset normal
        return Ride.objects.all().order_by('-departure_date', '-departure_time')

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

