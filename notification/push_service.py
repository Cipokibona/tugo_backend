import json
import logging

from django.conf import settings

from .models import PushSubscription

logger = logging.getLogger(__name__)

try:
    from pywebpush import WebPushException, webpush
except Exception:  # pragma: no cover - optional dependency fallback
    WebPushException = Exception
    webpush = None


def send_push_notification(notification):
    if not notification.recipient:
        return

    if not webpush:
        logger.warning('pywebpush is not installed; skipping push notification dispatch.')
        return

    public_key = getattr(settings, 'VAPID_PUBLIC_KEY', '')
    private_key = getattr(settings, 'VAPID_PRIVATE_KEY', '')
    claims_sub = getattr(settings, 'VAPID_CLAIMS_SUB', 'mailto:admin@example.com')

    if not public_key or not private_key:
        logger.warning('VAPID keys are not configured; skipping push notification dispatch.')
        return

    payload = json.dumps(
        {
            'title': notification.title,
            'body': notification.message,
            'notificationId': notification.id,
            'url': '/notifications',
            'type': notification.notification_type,
        }
    )

    subscriptions = PushSubscription.objects.filter(user=notification.recipient, is_active=True)
    for subscription in subscriptions:
        subscription_info = {
            'endpoint': subscription.endpoint,
            'keys': {
                'p256dh': subscription.p256dh,
                'auth': subscription.auth,
            },
        }

        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=private_key,
                vapid_claims={'sub': claims_sub},
                ttl=3600,
            )
        except WebPushException:
            # Subscription invalid/expired; deactivate it to avoid repeated failures.
            subscription.is_active = False
            subscription.save(update_fields=['is_active', 'updated_at'])
