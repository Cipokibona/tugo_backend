import threading
from datetime import timedelta
from math import atan2, cos, radians, sin, sqrt

from django.db import close_old_connections
from django.db.models import Case, IntegerField, Q, When
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from notification.models import Notification
from .models import Ride, RideBooking, ServiceTaxi, Taxi
from .serializers import (
    RideBookingSerializer,
    RideSerializer,
    ServiceTaxiSerializer,
    TaxiSerializer,
)


def _schedule_taxi_timeout(service_taxi_id):
    def _handle_timeout():
        close_old_connections()
        try:
            service_taxi = ServiceTaxi.objects.select_related(
                'client',
                'taxi__driver'
            ).get(pk=service_taxi_id)
        except ServiceTaxi.DoesNotExist:
            close_old_connections()
            return

        if service_taxi.status != 'REQUESTED':
            close_old_connections()
            return

        service_taxi.status = 'CANCELLED'
        no_response_note = 'Request cancelled: no driver response after 1 minute.'
        if service_taxi.notes:
            service_taxi.notes = f"{service_taxi.notes}\n{no_response_note}"
        else:
            service_taxi.notes = no_response_note
        service_taxi.save(update_fields=['status', 'notes', 'updated_at'])

        driver = service_taxi.taxi.driver if service_taxi.taxi else None
        if service_taxi.client:
            Notification.objects.create(
                recipient=service_taxi.client,
                sender=driver,
                title='Driver not available',
                message=(
                    f"No response from driver for your taxi request "
                    f"({service_taxi.pickup_location} at "
                    f"{service_taxi.pickup_date or 'N/A'} {service_taxi.pickup_time or 'N/A'})."
                ),
                notification_type='SERVICE_TAXI_TIMEOUT',
                service_taxi=service_taxi,
                action_required=False,
            )
        close_old_connections()

    timer = threading.Timer(60, _handle_timeout)
    timer.daemon = True
    timer.start()


class RideViewSet(viewsets.ModelViewSet):
    queryset = Ride.objects.all().order_by('-departure_date', '-departure_time')
    serializer_class = RideSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        now = timezone.localtime()
        closed_cutoff = now - timedelta(hours=1)

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
        ride_status = serializer.validated_data.get('status', 'OPEN')

        if ride_status == 'PROPOSED':
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


class TaxiViewSet(viewsets.ModelViewSet):
    queryset = Taxi.objects.all().order_by('-created_at')
    serializer_class = TaxiSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Taxi.objects.all().order_by('-created_at')

        mine = self.request.query_params.get('mine')
        available = self.request.query_params.get('available')
        latitude = self.request.query_params.get('latitude')
        longitude = self.request.query_params.get('longitude')
        radius_km = self.request.query_params.get('radius_km')

        if mine == 'true':
            queryset = queryset.filter(driver=self.request.user)

        if available is None:
            if mine != 'true':
                queryset = queryset.filter(is_active=True)
        elif available.lower() == 'true':
            queryset = queryset.filter(is_active=True)

        if latitude is not None and longitude is not None:
            try:
                client_lat = float(latitude)
                client_lng = float(longitude)
                max_radius = float(radius_km) if radius_km is not None else 5.0
            except ValueError:
                return queryset.none()

            def distance_in_km(taxi_lat, taxi_lng):
                earth_radius = 6371.0
                d_lat = radians(taxi_lat - client_lat)
                d_lng = radians(taxi_lng - client_lng)
                a = (
                    sin(d_lat / 2) ** 2
                    + cos(radians(client_lat))
                    * cos(radians(taxi_lat))
                    * sin(d_lng / 2) ** 2
                )
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                return earth_radius * c

            candidates = queryset.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
            nearby_items = []
            for taxi in candidates:
                distance = distance_in_km(taxi.latitude, taxi.longitude)
                if distance <= max_radius:
                    nearby_items.append((taxi.id, distance))

            if not nearby_items:
                return queryset.none()

            nearby_items.sort(key=lambda item: item[1])
            ordered_ids = [item[0] for item in nearby_items]
            order_case = Case(
                *[When(pk=pk, then=pos) for pos, pk in enumerate(ordered_ids)],
                output_field=IntegerField(),
            )
            queryset = queryset.filter(pk__in=ordered_ids).order_by(order_case)

        return queryset

    def perform_create(self, serializer):
        serializer.save(driver=self.request.user)


class ServiceTaxiViewSet(viewsets.ModelViewSet):
    queryset = ServiceTaxi.objects.all().order_by('-created_at')
    serializer_class = ServiceTaxiSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ServiceTaxi.objects.filter(
            Q(client=self.request.user)
            | Q(taxi__driver=self.request.user)
        ).order_by('-created_at')

    def perform_create(self, serializer):
        service_taxi = serializer.save(client=self.request.user)

        recipient = service_taxi.taxi.driver if service_taxi.taxi else None
        if recipient and recipient != self.request.user:
            Notification.objects.create(
                recipient=recipient,
                sender=self.request.user,
                title='New taxi request',
                message=(
                    f"{self.request.user.username} requested a taxi from "
                    f"{service_taxi.pickup_location} to {service_taxi.dropoff_location}. "
                    f"Pickup: {service_taxi.pickup_date or 'N/A'} at "
                    f"{service_taxi.pickup_time or 'N/A'}."
                ),
                notification_type='SERVICE_TAXI_REQUESTED',
                service_taxi=service_taxi,
                action_required=True,
            )

        _schedule_taxi_timeout(service_taxi.id)

    @action(detail=True, methods=['post'], url_path='driver-response')
    def driver_response(self, request, pk=None):
        service_taxi = self.get_object()
        driver = service_taxi.taxi.driver if service_taxi.taxi else None
        if driver != request.user:
            return Response(
                {'detail': 'Only the taxi driver can respond to this request.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if service_taxi.status != 'REQUESTED':
            return Response(
                {'detail': 'This taxi request has already been handled.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        decision = (request.data.get('decision') or '').upper()
        if decision not in ['ACCEPT', 'REJECT']:
            return Response(
                {'detail': "Decision must be either 'ACCEPT' or 'REJECT'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if decision == 'ACCEPT':
            service_taxi.status = 'ACCEPTED'
            title = 'Taxi request accepted'
            message = (
                f"{request.user.username} accepted your taxi request "
                f"for {service_taxi.pickup_location} on "
                f"{service_taxi.pickup_date or 'N/A'} at "
                f"{service_taxi.pickup_time or 'N/A'}."
            )
            notification_type = 'SERVICE_TAXI_ACCEPTED'
        else:
            service_taxi.status = 'CANCELLED'
            title = 'Taxi request rejected'
            message = (
                f"{request.user.username} rejected your taxi request "
                f"for {service_taxi.pickup_location} on "
                f"{service_taxi.pickup_date or 'N/A'} at "
                f"{service_taxi.pickup_time or 'N/A'}."
            )
            notification_type = 'SERVICE_TAXI_REJECTED'

        service_taxi.save(update_fields=['status', 'updated_at'])

        Notification.objects.filter(
            service_taxi=service_taxi,
            notification_type='SERVICE_TAXI_REQUESTED',
        ).update(is_read=True, action_required=False)

        if service_taxi.client:
            Notification.objects.create(
                recipient=service_taxi.client,
                sender=request.user,
                title=title,
                message=message,
                notification_type=notification_type,
                service_taxi=service_taxi,
                action_required=False,
            )

        return Response(self.get_serializer(service_taxi).data, status=status.HTTP_200_OK)
