from rest_framework.routers import DefaultRouter
from .views import RideViewSet, RideBookingViewSet, TaxiViewSet, ServiceTaxiViewSet

router = DefaultRouter()
router.register(r'rides', RideViewSet)
router.register(r'bookings', RideBookingViewSet)
router.register(r'taxis', TaxiViewSet)
router.register(r'service-taxis', ServiceTaxiViewSet)

urlpatterns = router.urls
