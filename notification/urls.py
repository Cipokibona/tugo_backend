from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import NotificationViewSet, PushPublicKeyView, PushSubscriptionView

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    *router.urls,
    path('push-subscriptions/', PushSubscriptionView.as_view(), name='push-subscriptions'),
    path('push-public-key/', PushPublicKeyView.as_view(), name='push-public-key'),
]
