# security/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from django.http import HttpResponse
import csv
import io

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
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por tipo de reporte si se especifica
        report_type = self.request.query_params.get('report_type', None)
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        
        # Filtrar por estado
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
        
        # Filtrar por severidad
        severity = self.request.query_params.get('severity', None)
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # Filtrar por fecha
        days = self.request.query_params.get('days', None)
        if days:
            date_from = timezone.now() - timedelta(days=int(days))
            queryset = queryset.filter(created_at__gte=date_from)
        
        return queryset
    
    def perform_create(self, serializer):
        # Asignar automáticamente el usuario que reporta
        serializer.save(reported_by=self.request.user)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def create_alert(self, request):
        """Endpoint simplificado para crear alertas desde el dashboard de usuario"""
        data = request.data
        
        # Mapear el tipo de alerta al tipo de reporte
        alert_type = data.get('type', 'Reporte')
        report_type_map = {
            'Emergencia': 'emergency',
            'Seguridad': 'alert',
            'Reporte': 'general'
        }
        
        # Determinar severidad basada en el tipo
        severity_map = {
            'Emergencia': 'high',
            'Seguridad': 'medium',
            'Reporte': 'low'
        }
        
        # Crear el incidente/reporte
        incident_data = {
            'title': f"{alert_type}: {data.get('message', '')[:50]}...",
            'description': data.get('message', ''),
            'location': 'Reportado desde dashboard de usuario',
            'severity': severity_map.get(alert_type, 'medium'),
            'report_type': report_type_map.get(alert_type, 'general'),
            'reported_by': request.user.id
        }
        
        serializer = SecurityIncidentSerializer(data=incident_data)
        if serializer.is_valid():
            serializer.save(reported_by=request.user)
            return Response({
                'success': True,
                'message': 'Alerta enviada correctamente',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Estadísticas para el dashboard de reportes"""
        # Últimos 30 días
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Todos los reportes
        all_reports = SecurityIncident.objects.all()
        recent_reports = all_reports.filter(created_at__gte=thirty_days_ago)
        
        # Estadísticas por tipo
        stats = {
            'total_reports': all_reports.count(),
            'recent_reports': recent_reports.count(),
            'by_type': {
                'alerts': all_reports.filter(report_type='alert').count(),
                'emergencies': all_reports.filter(report_type='emergency').count(),
                'incidents': all_reports.filter(report_type='incident').count(),
                'general': all_reports.filter(report_type='general').count(),
            },
            'by_status': {
                'new': all_reports.filter(status='new').count(),
                'in_progress': all_reports.filter(status='in_progress').count(),
                'resolved': all_reports.filter(status='resolved').count(),
                'closed': all_reports.filter(status='closed').count(),
            },
            'by_severity': {
                'critical': all_reports.filter(severity='critical').count(),
                'high': all_reports.filter(severity='high').count(),
                'medium': all_reports.filter(severity='medium').count(),
                'low': all_reports.filter(severity='low').count(),
            },
            'recent_by_day': [],
            'top_reporters': []
        }
        
        # Reportes por día (últimos 7 días)
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            count = all_reports.filter(created_at__date=date).count()
            stats['recent_by_day'].append({
                'date': date.isoformat(),
                'count': count
            })
        
        # Top 5 reportadores
        top_reporters = all_reports.values('reported_by__username', 'reported_by__first_name', 'reported_by__last_name')\
            .annotate(count=Count('id'))\
            .order_by('-count')[:5]
        
        stats['top_reporters'] = [
            {
                'username': r['reported_by__username'],
                'name': f"{r['reported_by__first_name'] or ''} {r['reported_by__last_name'] or ''}".strip() or r['reported_by__username'],
                'count': r['count']
            }
            for r in top_reporters
        ]
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Exportar reportes a CSV"""
        # Obtener reportes filtrados
        queryset = self.filter_queryset(self.get_queryset())
        
        # Crear CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        writer.writerow([
            'ID', 'Tipo', 'Título', 'Descripción', 'Ubicación', 
            'Severidad', 'Estado', 'Reportado por', 'Fecha de creación'
        ])
        
        # Datos
        for report in queryset:
            writer.writerow([
                report.id,
                report.get_report_type_display(),
                report.title,
                report.description,
                report.location,
                report.get_severity_display(),
                report.get_status_display(),
                report.reported_by.get_full_name() or report.reported_by.username,
                report.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        output.seek(0)
        response = HttpResponse(output, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="reportes_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        return response
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Cambiar el estado de un reporte"""
        incident = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in ['new', 'in_progress', 'resolved', 'closed']:
            return Response({
                'error': 'Estado inválido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        old_status = incident.status
        incident.status = new_status
        
        # Si se resuelve, marcar la fecha
        if new_status == 'resolved' and old_status != 'resolved':
            incident.resolved_at = timezone.now()
        
        incident.save()
        
        # Añadir comentario del sistema
        incident.comments.create(
            user=request.user,
            comment=f"Estado cambiado de {old_status} a {new_status}",
            is_system_comment=True
        )
        
        return Response({
            'success': True,
            'message': 'Estado actualizado correctamente'
        })
    
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