from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.permissions import IsAuthenticated

# Creación de vistas simples para los modelos de security
from rest_framework import viewsets
from .models import (
    SecurityIncident, 
    EmergencyProtocol,
    EmergencyEvent,
    SecurityCheckpoint,
    SecurityRound,
    SecurityRoundExecution
)
from rest_framework import serializers

# Serializers
class SecurityIncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityIncident
        fields = '__all__'

class EmergencyProtocolSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyProtocol
        fields = '__all__'

class EmergencyEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyEvent
        fields = '__all__'

class SecurityCheckpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityCheckpoint
        fields = '__all__'

class SecurityRoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityRound
        fields = '__all__'

class SecurityRoundExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityRoundExecution
        fields = '__all__'

# ViewSets
class SecurityIncidentViewSet(viewsets.ModelViewSet):
    queryset = SecurityIncident.objects.all()
    serializer_class = SecurityIncidentSerializer
    permission_classes = [IsAuthenticated]

class EmergencyProtocolViewSet(viewsets.ModelViewSet):
    queryset = EmergencyProtocol.objects.all()
    serializer_class = EmergencyProtocolSerializer
    permission_classes = [IsAuthenticated]

class EmergencyEventViewSet(viewsets.ModelViewSet):
    queryset = EmergencyEvent.objects.all()
    serializer_class = EmergencyEventSerializer
    permission_classes = [IsAuthenticated]

class SecurityCheckpointViewSet(viewsets.ModelViewSet):
    queryset = SecurityCheckpoint.objects.all()
    serializer_class = SecurityCheckpointSerializer
    permission_classes = [IsAuthenticated]

class SecurityRoundViewSet(viewsets.ModelViewSet):
    queryset = SecurityRound.objects.all()
    serializer_class = SecurityRoundSerializer
    permission_classes = [IsAuthenticated]

class SecurityRoundExecutionViewSet(viewsets.ModelViewSet):
    queryset = SecurityRoundExecution.objects.all()
    serializer_class = SecurityRoundExecutionSerializer
    permission_classes = [IsAuthenticated]

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