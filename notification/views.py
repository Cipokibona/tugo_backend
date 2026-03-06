from datetime import datetime, timezone

from django.conf import settings
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, PushSubscription
from .push_service import send_push_notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    def perform_create(self, serializer):
        notification = serializer.save(sender=self.request.user)
        send_push_notification(notification)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=['is_read'])
        return Response(self.get_serializer(notification).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'detail': 'All notifications marked as read.'}, status=status.HTTP_200_OK)


class PushPublicKeyView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({'public_key': getattr(settings, 'VAPID_PUBLIC_KEY', '')}, status=status.HTTP_200_OK)


class PushSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        endpoint = request.data.get('endpoint')
        keys = request.data.get('keys') or {}
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')

        if not endpoint or not p256dh or not auth:
            return Response(
                {'detail': 'endpoint, keys.p256dh, and keys.auth are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expiration_time = self._resolve_expiration_time(request.data.get('expirationTime'))

        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                'user': request.user,
                'p256dh': p256dh,
                'auth': auth,
                'expiration_time': expiration_time,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'is_active': True,
            },
        )

        return Response({'detail': 'Push subscription saved.'}, status=status.HTTP_200_OK)

    def delete(self, request):
        endpoint = request.data.get('endpoint')
        queryset = PushSubscription.objects.filter(user=request.user)
        if endpoint:
            queryset = queryset.filter(endpoint=endpoint)

        deleted_count, _ = queryset.delete()
        return Response({'deleted': deleted_count}, status=status.HTTP_200_OK)

    @staticmethod
    def _resolve_expiration_time(raw_expiration):
        if raw_expiration in [None, '']:
            return None

        if isinstance(raw_expiration, (int, float)):
            try:
                return datetime.fromtimestamp(raw_expiration / 1000, tz=timezone.utc)
            except Exception:
                return None

        if isinstance(raw_expiration, str):
            # Accept ISO string format if provided by client.
            try:
                cleaned = raw_expiration.replace('Z', '+00:00')
                return datetime.fromisoformat(cleaned)
            except Exception:
                return None

        return None
