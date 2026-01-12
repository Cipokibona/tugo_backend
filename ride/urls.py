from rest_framework.routers import DefaultRouter
from .views import RideViewSet, RideBookingViewSet

router = DefaultRouter()
router.register(r'rides', RideViewSet)
router.register(r'bookings', RideBookingViewSet)

urlpatterns = router.urls
