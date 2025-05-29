# security/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SecurityIncidentViewSet,
    EmergencyProtocolViewSet,
    EmergencyEventViewSet,
    SecurityCheckpointViewSet,
    SecurityRoundViewSet,
    SecurityRoundExecutionViewSet
)

# Router
router = DefaultRouter()
router.register(r'incidents', SecurityIncidentViewSet)
router.register(r'protocols', EmergencyProtocolViewSet)
router.register(r'events', EmergencyEventViewSet)
router.register(r'checkpoints', SecurityCheckpointViewSet)
router.register(r'rounds', SecurityRoundViewSet)
router.register(r'executions', SecurityRoundExecutionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]