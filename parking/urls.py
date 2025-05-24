from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ParkingAreaViewSet,
    VehicleViewSet,
    ParkingAccessViewSet,
    ParkingLogViewSet,
    check_access,
    register_entry,
    register_exit
)

# Router
router = DefaultRouter()
router.register(r'areas', ParkingAreaViewSet)
router.register(r'vehicles', VehicleViewSet)
router.register(r'access', ParkingAccessViewSet)
router.register(r'logs', ParkingLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('check-access/', check_access, name='check-access'),
    path('register-entry/', register_entry, name='register-entry'),
    path('register-exit/', register_exit, name='register-exit'),
]