# security/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count

from .models import (
    SecurityIncident, 
    EmergencyProtocol,
    EmergencyEvent,
    SecurityCheckpoint,
    SecurityRound,
    SecurityRoundExecution
)
from .serializers import (
    SecurityIncidentSerializer,
    EmergencyProtocolSerializer,
    EmergencyEventSerializer,
    SecurityCheckpointSerializer,
    SecurityRoundSerializer,
    SecurityRoundExecutionSerializer
)

class SecurityIncidentViewSet(viewsets.ModelViewSet):
    queryset = SecurityIncident.objects.all().order_by('-created_at')
    serializer_class = SecurityIncidentSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def user_report(self, request):
        """Genera un reporte simple para usuarios sobre incidentes que han reportado"""
        # Obtener incidentes del usuario
        user_incidents = SecurityIncident.objects.filter(reported_by=request.user)
        
        # Estadísticas básicas
        stats = {
            'total_reported': user_incidents.count(),
            'by_status': {
                'new': user_incidents.filter(status='new').count(),
                'in_progress': user_incidents.filter(status='in_progress').count(),
                'resolved': user_incidents.filter(status='resolved').count(),
                'closed': user_incidents.filter(status='closed').count()
            },
            'by_severity': {
                'critical': user_incidents.filter(severity='critical').count(),
                'high': user_incidents.filter(severity='high').count(),
                'medium': user_incidents.filter(severity='medium').count(),
                'low': user_incidents.filter(severity='low').count()
            },
            'last_30_days': user_incidents.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'recent_incidents': SecurityIncidentSerializer(
                user_incidents[:5], 
                many=True
            ).data
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Resumen general de incidentes (para dashboard)"""
        # Últimos 30 días
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        incidents = SecurityIncident.objects.filter(
            created_at__gte=thirty_days_ago
        )
        
        summary = {
            'total': incidents.count(),
            'new': incidents.filter(status='new').count(),
            'in_progress': incidents.filter(status='in_progress').count(),
            'resolved': incidents.filter(status='resolved').count(),
            'critical': incidents.filter(severity='critical').count(),
            'high': incidents.filter(severity='high').count()
        }
        
        return Response(summary)

class EmergencyProtocolViewSet(viewsets.ModelViewSet):
    queryset = EmergencyProtocol.objects.all()
    serializer_class = EmergencyProtocolSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

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
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class SecurityRoundExecutionViewSet(viewsets.ModelViewSet):
    queryset = SecurityRoundExecution.objects.all()
    serializer_class = SecurityRoundExecutionSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def my_rounds(self, request):
        """Obtiene las rondas ejecutadas por el usuario actual"""
        my_rounds = SecurityRoundExecution.objects.filter(
            guard=request.user
        ).order_by('-start_time')[:10]
        
        serializer = self.get_serializer(my_rounds, many=True)
        return Response(serializer.data)