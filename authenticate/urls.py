from rest_framework.routers import DefaultRouter
from .views import UserViewSet, DriverProfileViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'driver-profiles', DriverProfileViewSet)

urlpatterns = router.urls
