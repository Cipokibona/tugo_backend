from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import AfripayCheckoutLaunchView, AfripayCheckoutProxyView, GameScoreViewSet, RideViewSet, RideBookingViewSet, TaxiViewSet, ServiceTaxiViewSet

router = DefaultRouter()
router.register(r'rides', RideViewSet)
router.register(r'bookings', RideBookingViewSet)
router.register(r'taxis', TaxiViewSet)
router.register(r'service-taxis', ServiceTaxiViewSet)
router.register(r'game-scores', GameScoreViewSet, basename='game-score')

urlpatterns = [
    path('afripay/checkout/', AfripayCheckoutProxyView.as_view(), name='afripay-checkout'),
    path('afripay/checkout/launch/<str:token>/', AfripayCheckoutLaunchView.as_view(), name='afripay-checkout-launch'),
    *router.urls,
]
