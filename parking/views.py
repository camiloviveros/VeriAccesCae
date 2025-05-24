from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Count, F
from django.db import transaction
from datetime import datetime
from django.utils import timezone

from .models import ParkingArea, Vehicle, ParkingAccess, ParkingLog
from .serializers import (
    ParkingAreaSerializer, 
    VehicleSerializer, 
    ParkingAccessSerializer, 
    ParkingLogSerializer
)


class ParkingAreaViewSet(viewsets.ModelViewSet):
    queryset = ParkingArea.objects.all()
    serializer_class = ParkingAreaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrar solo áreas activas por defecto
        active_only = self.request.query_params.get('active_only', 'false')
        if active_only.lower() == 'true' or not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('name')
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtener estadísticas generales del estacionamiento"""
        areas = self.get_queryset()
        total_capacity = sum(area.max_capacity for area in areas)
        current_occupancy = sum(area.current_count for area in areas)
        
        area_stats = []
        for area in areas:
            area_stats.append({
                'id': area.id,
                'name': area.name,
                'capacity': area.max_capacity,
                'occupied': area.current_count,
                'available': area.max_capacity - area.current_count
            })
        
        return Response({
            'total_capacity': total_capacity,
            'current_occupancy': current_occupancy,
            'available_spots': total_capacity - current_occupancy,
            'occupancy_percentage': (current_occupancy / total_capacity * 100) if total_capacity > 0 else 0,
            'areas': area_stats
        })


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filtrar vehículos por usuario si no es admin
        user = self.request.user
        queryset = super().get_queryset().select_related('user', 'parking_area')
        
        if user.is_staff or user.is_superuser:
            # Los admins pueden ver todos los vehículos
            # Opcionalmente filtrar por usuario específico
            user_id = self.request.query_params.get('user_id', None)
            if user_id:
                queryset = queryset.filter(user_id=user_id)
        else:
            # Los usuarios normales solo ven sus propios vehículos
            queryset = queryset.filter(user=user)
            
        # Filtros adicionales
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        # Búsqueda por placa
        license_plate = self.request.query_params.get('license_plate', None)
        if license_plate:
            queryset = queryset.filter(license_plate__icontains=license_plate)
        
        # Filtrar por área de estacionamiento
        parking_area_id = self.request.query_params.get('parking_area_id', None)
        if parking_area_id:
            queryset = queryset.filter(parking_area_id=parking_area_id)
            
        return queryset.order_by('-created_at')
    
    @transaction.atomic
    def perform_create(self, serializer):
        """Crear vehículo y actualizar contador del área"""
        # Automáticamente asignar el usuario actual al crear un vehículo
        vehicle = serializer.save(user=self.request.user)
        
        # Incrementar contador del área de estacionamiento
        parking_area = vehicle.parking_area
        parking_area.current_count = F('current_count') + 1
        parking_area.save()
        
        # Actualizar el objeto para obtener el valor real
        parking_area.refresh_from_db()
        
        # Crear acceso automático al área asignada
        ParkingAccess.objects.get_or_create(
            vehicle=vehicle,
            parking_area=parking_area,
            defaults={'valid_from': timezone.now().date()}
        )
        
    @transaction.atomic
    def perform_update(self, serializer):
        """Actualizar vehículo y manejar cambio de área"""
        old_instance = self.get_object()
        old_parking_area = old_instance.parking_area
        
        # Asegurar que no se pueda cambiar el usuario propietario
        if 'user' in serializer.validated_data:
            del serializer.validated_data['user']
            
        updated_vehicle = serializer.save()
        new_parking_area = updated_vehicle.parking_area
        
        # Si cambió el área de estacionamiento
        if old_parking_area != new_parking_area:
            # Decrementar contador del área anterior
            old_parking_area.current_count = F('current_count') - 1
            old_parking_area.save()
            
            # Incrementar contador del área nueva
            new_parking_area.current_count = F('current_count') + 1
            new_parking_area.save()
            
            # Crear nuevo acceso y desactivar el anterior si existe
            old_access = ParkingAccess.objects.filter(
                vehicle=updated_vehicle,
                parking_area=old_parking_area
            ).first()
            if old_access:
                old_access.valid_to = timezone.now().date()
                old_access.save()
            
            # Crear nuevo acceso
            ParkingAccess.objects.get_or_create(
                vehicle=updated_vehicle,
                parking_area=new_parking_area,
                defaults={'valid_from': timezone.now().date()}
            )
    
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """Override destroy para manejar contadores y permisos"""
        instance = self.get_object()
        
        # Verificar permisos - solo el propietario o admin puede eliminar
        if not request.user.is_staff and instance.user != request.user:
            return Response(
                {'error': 'No tienes permiso para eliminar este vehículo'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Guardar referencia al área antes de eliminar
        parking_area = instance.parking_area
        
        # Eliminar el vehículo
        self.perform_destroy(instance)
        
        # Decrementar contador del área de estacionamiento
        if parking_area.current_count > 0:
            parking_area.current_count = F('current_count') - 1
            parking_area.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Activar/desactivar un vehículo (marcar dentro/fuera del área)"""
        vehicle = self.get_object()
        
        # Verificar permisos
        if not request.user.is_staff and vehicle.user != request.user:
            return Response(
                {'error': 'No tienes permiso para cambiar el estado de este vehículo'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        vehicle.is_active = not vehicle.is_active
        vehicle.save()
        
        # Registrar en el log
        direction = 'in' if vehicle.is_active else 'out'
        ParkingLog.objects.create(
            vehicle=vehicle,
            parking_area=vehicle.parking_area,
            direction=direction,
            status='granted',
            reason=f'Cambio manual de estado por {request.user.username}'
        )
        
        return Response({
            'status': 'success',
            'is_active': vehicle.is_active,
            'message': f'Vehículo marcado como {"adentro" if vehicle.is_active else "afuera"}'
        })


class ParkingAccessViewSet(viewsets.ModelViewSet):
    queryset = ParkingAccess.objects.all()
    serializer_class = ParkingAccessSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        if not user.is_staff:
            # Los usuarios normales solo ven los accesos de sus vehículos
            queryset = queryset.filter(vehicle__user=user)
            
        # Filtros opcionales
        vehicle_id = self.request.query_params.get('vehicle_id', None)
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
            
        parking_area_id = self.request.query_params.get('parking_area_id', None)
        if parking_area_id:
            queryset = queryset.filter(parking_area_id=parking_area_id)
            
        # Filtrar solo accesos válidos (sin fecha de fin o fecha de fin futura)
        active_only = self.request.query_params.get('active_only', 'true')
        if active_only.lower() == 'true':
            queryset = queryset.filter(
                Q(valid_to__isnull=True) | Q(valid_to__gte=timezone.now().date())
            )
            
        return queryset.order_by('-valid_from')


class ParkingLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ParkingLog.objects.all()
    serializer_class = ParkingLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        if not user.is_staff:
            # Los usuarios normales solo ven los logs de sus vehículos
            queryset = queryset.filter(vehicle__user=user)
            
        # Filtros opcionales
        vehicle_id = self.request.query_params.get('vehicle_id', None)
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
            
        parking_area_id = self.request.query_params.get('parking_area_id', None)
        if parking_area_id:
            queryset = queryset.filter(parking_area_id=parking_area_id)
            
        direction = self.request.query_params.get('direction', None)
        if direction in ['in', 'out']:
            queryset = queryset.filter(direction=direction)
            
        status_filter = self.request.query_params.get('status', None)
        if status_filter in ['granted', 'denied']:
            queryset = queryset.filter(status=status_filter)
            
        # Filtro por rango de fechas
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)
            
        return queryset.order_by('-timestamp')


# Vistas adicionales para funcionalidades específicas
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_access(request):
    """Verificar si un vehículo tiene acceso a un área de estacionamiento"""
    vehicle_id = request.data.get('vehicle')
    parking_area_id = request.data.get('parking_area')
    
    if not vehicle_id or not parking_area_id:
        return Response({
            'error': 'Se requiere vehicle y parking_area'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        vehicle = Vehicle.objects.get(id=vehicle_id)
        parking_area = ParkingArea.objects.get(id=parking_area_id)
        
        # Verificar si el vehículo pertenece al usuario (si no es admin)
        if not request.user.is_staff and vehicle.user != request.user:
            return Response({
                'error': 'No tienes permiso para verificar este vehículo'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Verificar si existe un acceso válido
        has_access = ParkingAccess.objects.filter(
            vehicle=vehicle,
            parking_area=parking_area,
            valid_from__lte=timezone.now().date()
        ).filter(
            Q(valid_to__isnull=True) | Q(valid_to__gte=timezone.now().date())
        ).exists()
        
        return Response({
            'has_access': has_access,
            'vehicle': vehicle.license_plate,
            'area': parking_area.name
        })
        
    except Vehicle.DoesNotExist:
        return Response({
            'error': 'Vehículo no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except ParkingArea.DoesNotExist:
        return Response({
            'error': 'Área de estacionamiento no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def register_entry(request):
    """Registrar entrada de un vehículo al estacionamiento"""
    vehicle_id = request.data.get('vehicle')
    parking_area_id = request.data.get('parking_area')
    
    if not vehicle_id or not parking_area_id:
        return Response({
            'error': 'Se requiere vehicle y parking_area'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        vehicle = Vehicle.objects.get(id=vehicle_id)
        parking_area = ParkingArea.objects.get(id=parking_area_id)
        
        # Verificar permisos
        if not request.user.is_staff and vehicle.user != request.user:
            return Response({
                'error': 'No tienes permiso para registrar este vehículo'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Verificar acceso
        has_access = ParkingAccess.objects.filter(
            vehicle=vehicle,
            parking_area=parking_area,
            valid_from__lte=timezone.now().date()
        ).filter(
            Q(valid_to__isnull=True) | Q(valid_to__gte=timezone.now().date())
        ).exists()
        
        if not has_access:
            # Registrar intento denegado
            log = ParkingLog.objects.create(
                vehicle=vehicle,
                parking_area=parking_area,
                direction='in',
                status='denied',
                reason='No tiene acceso autorizado'
            )
            return Response({
                'status': 'denied',
                'reason': 'No tiene acceso autorizado',
                'log_id': log.id
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Verificar capacidad
        if parking_area.current_count >= parking_area.max_capacity:
            log = ParkingLog.objects.create(
                vehicle=vehicle,
                parking_area=parking_area,
                direction='in',
                status='denied',
                reason='Estacionamiento lleno'
            )
            return Response({
                'status': 'denied',
                'reason': 'Estacionamiento lleno',
                'log_id': log.id
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Registrar entrada exitosa
        log = ParkingLog.objects.create(
            vehicle=vehicle,
            parking_area=parking_area,
            direction='in',
            status='granted'
        )
        
        return Response({
            'status': 'granted',
            'log_id': log.id,
            'message': f'Entrada registrada para {vehicle.license_plate}'
        }, status=status.HTTP_201_CREATED)
        
    except Vehicle.DoesNotExist:
        return Response({
            'error': 'Vehículo no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except ParkingArea.DoesNotExist:
        return Response({
            'error': 'Área de estacionamiento no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def register_exit(request):
    """Registrar salida de un vehículo del estacionamiento"""
    vehicle_id = request.data.get('vehicle')
    parking_area_id = request.data.get('parking_area')
    
    if not vehicle_id or not parking_area_id:
        return Response({
            'error': 'Se requiere vehicle y parking_area'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        vehicle = Vehicle.objects.get(id=vehicle_id)
        parking_area = ParkingArea.objects.get(id=parking_area_id)
        
        # Verificar permisos
        if not request.user.is_staff and vehicle.user != request.user:
            return Response({
                'error': 'No tienes permiso para registrar este vehículo'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Registrar salida
        log = ParkingLog.objects.create(
            vehicle=vehicle,
            parking_area=parking_area,
            direction='out',
            status='granted'
        )
        
        return Response({
            'status': 'granted',
            'log_id': log.id,
            'message': f'Salida registrada para {vehicle.license_plate}'
        }, status=status.HTTP_201_CREATED)
        
    except Vehicle.DoesNotExist:
        return Response({
            'error': 'Vehículo no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except ParkingArea.DoesNotExist:
        return Response({
            'error': 'Área de estacionamiento no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)