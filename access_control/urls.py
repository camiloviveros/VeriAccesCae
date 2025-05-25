from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AccessPointViewSet,
    AccessZoneViewSet,
    AccessCardViewSet,
    AccessPermissionViewSet,
    AccessLogViewSet,
    VisitorViewSet,
    VisitorAccessViewSet,
    BuildingOccupancyViewSet
)

# Configuración del router para viewsets
router = DefaultRouter()
router.register(r'access-points', AccessPointViewSet)
router.register(r'access-zones', AccessZoneViewSet)
router.register(r'access-cards', AccessCardViewSet)
router.register(r'access-permissions', AccessPermissionViewSet)
router.register(r'access-logs', AccessLogViewSet)
router.register(r'visitors', VisitorViewSet)
router.register(r'visitor-access', VisitorAccessViewSet)
router.register(r'occupancy', BuildingOccupancyViewSet)

urlpatterns = [
    # Incluir todas las rutas del router
    path('', include(router.urls)),
]