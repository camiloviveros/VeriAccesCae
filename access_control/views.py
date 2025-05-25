from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
import datetime
import uuid
import json

from authentication.models import User
from .models import (
    AccessPoint, 
    AccessZone, 
    AccessCard, 
    AccessPermission, 
    AccessLog, 
    Visitor, 
    VisitorAccess,
    BuildingOccupancy
)
from .serializers import (
    AccessPointSerializer,
    AccessZoneSerializer,
    AccessCardSerializer,
    AccessPermissionSerializer,
    AccessLogSerializer,
    VisitorSerializer,
    VisitorAccessSerializer,
    BuildingOccupancySerializer
)
from .permissions import IsSecurityPersonnel, IsReceptionist, IsAdministrator
from django.shortcuts import get_object_or_404
import qrcode
import io
import base64
from django.core.files.base import ContentFile
from rest_framework.exceptions import ValidationError

class AccessPointViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar puntos de acceso.
    """
    queryset = AccessPoint.objects.all()
    serializer_class = AccessPointSerializer
    permission_classes = [IsAuthenticated, IsAdministrator]
    filterset_fields = ['name', 'location', 'is_active']
    search_fields = ['name', 'description', 'location']
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSecurityPersonnel])
    def remote_control(self, request, pk=None):
        """
        Permite al personal de seguridad bloquear/desbloquear remotamente un punto de acceso.
        """
        access_point = self.get_object()
        action = request.data.get('action')
        
        if action not in ['lock', 'unlock']:
            return Response(
                {'error': 'Acción no válida. Use "lock" o "unlock"'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Aquí iría la lógica para interactuar con el hardware real
        # Por ahora, solo simularemos que la acción fue exitosa
        
        message = f"Punto de acceso {access_point.name} {'bloqueado' if action == 'lock' else 'desbloqueado'} correctamente"
        
        # Registrar la acción en el log
        AccessLog.objects.create(
            user=request.user,
            access_point=access_point,
            status='granted',
            reason=f"Control remoto: {action}",
            direction='none'
        )
        
        return Response({'detail': message}, status=status.HTTP_200_OK)
        
    @action(detail=True, methods=['get'])
    def current_status(self, request, pk=None):
        """
        Obtiene el estado actual del punto de acceso.
        """
        access_point = self.get_object()
        return Response({
            'id': access_point.id,
            'name': access_point.name,
            'is_active': access_point.is_active,
            'current_count': access_point.current_count,
            'max_capacity': access_point.max_capacity,
            'is_at_capacity': access_point.current_count >= access_point.max_capacity if access_point.max_capacity > 0 else False
        })

    def destroy(self, request, *args, **kwargs):
        """
        Sobrescribe el método de eliminación para mejorar el manejo de errores
        """
        try:
            instance = self.get_object()
            # Registrar la eliminación para depuración
            print(f"Eliminando punto de acceso: {instance.id} - {instance.name}")
            
            # Realizar la eliminación
            self.perform_destroy(instance)
            
            # Registrar éxito
            print(f"Punto de acceso eliminado correctamente: {instance.id}")
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            # Registrar el error detallado
            print(f"Error al eliminar punto de acceso: {e}")
            # Devolver una respuesta detallada de error
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AccessZoneViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar zonas de acceso.
    """
    queryset = AccessZone.objects.all()
    serializer_class = AccessZoneSerializer
    permission_classes = [IsAuthenticated, IsAdministrator]
    filterset_fields = ['name']
    search_fields = ['name', 'description']
    
    @action(detail=True, methods=['get'])
    def access_points(self, request, pk=None):
        """
        Lista todos los puntos de acceso en una zona.
        """
        zone = self.get_object()
        access_points = zone.access_points.all()
        serializer = AccessPointSerializer(access_points, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def current_status(self, request, pk=None):
        """
        Obtiene el estado actual de la zona.
        """
        zone = self.get_object()
        return Response({
            'id': zone.id,
            'name': zone.name,
            'current_count': zone.current_count,
            'max_capacity': zone.max_capacity,
            'is_at_capacity': zone.current_count >= zone.max_capacity if zone.max_capacity > 0 else False
        })
        
    def destroy(self, request, *args, **kwargs):
        """
        Sobrescribe el método de eliminación para mejorar el manejo de errores
        """
        try:
            instance = self.get_object()
            # Registrar la eliminación para depuración
            print(f"Eliminando zona de acceso: {instance.id} - {instance.name}")
            
            # Realizar la eliminación
            self.perform_destroy(instance)
            
            # Registrar éxito
            print(f"Zona de acceso eliminada correctamente: {instance.id}")
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            # Registrar el error detallado
            print(f"Error al eliminar zona de acceso: {e}")
            # Devolver una respuesta detallada de error
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AccessCardViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar tarjetas de acceso.
    """
    queryset = AccessCard.objects.all()
    serializer_class = AccessCardSerializer
    permission_classes = [IsAuthenticated, IsAdministrator]
    filterset_fields = ['card_id', 'user', 'is_active']
    
    @action(detail=True, methods=['post'])
    def assign_to_user(self, request, pk=None):
        """
        Asigna una tarjeta a un usuario.
        """
        card = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'Se requiere user_id'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            card.user = user
            card.save()
            serializer = self.get_serializer(card)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def unassign(self, request, pk=None):
        """
        Desasigna la tarjeta del usuario actual.
        """
        card = self.get_object()
        card.user = None
        card.save()
        serializer = self.get_serializer(card)
        return Response(serializer.data)
        
    def destroy(self, request, *args, **kwargs):
        """
        Sobrescribe el método de eliminación para mejorar el manejo de errores
        """
        try:
            instance = self.get_object()
            # Registrar la eliminación para depuración
            print(f"Eliminando tarjeta de acceso: {instance.id} - {instance.card_id}")
            
            # Realizar la eliminación
            self.perform_destroy(instance)
            
            # Registrar éxito
            print(f"Tarjeta de acceso eliminada correctamente: {instance.id}")
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            # Registrar el error detallado
            print(f"Error al eliminar tarjeta de acceso: {e}")
            # Devolver una respuesta detallada de error
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AccessPermissionViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar permisos de acceso.
    """
    queryset = AccessPermission.objects.all()
    serializer_class = AccessPermissionSerializer
    permission_classes = [IsAuthenticated, IsAdministrator]
    filterset_fields = ['user', 'zone', 'is_active']
    
    @action(detail=False, methods=['get'])
    def my_permissions(self, request):
        """
        Devuelve los permisos de acceso del usuario actual.
        """
        permissions = AccessPermission.objects.filter(
            user=request.user, 
            is_active=True,
            valid_to__gte=datetime.date.today()
        )
        serializer = self.get_serializer(permissions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def check_permission(self, request):
        """
        Verifica si un usuario tiene permiso para acceder a una zona específica.
        """
        user_id = request.data.get('user_id')
        zone_id = request.data.get('zone_id')
        
        if not user_id or not zone_id:
            return Response(
                {'error': 'Se requieren user_id y zone_id'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            zone = AccessZone.objects.get(id=zone_id)
            
            now = timezone.now()
            current_time = now.time()
            
            # Verificar si existe un permiso activo para el usuario en esta zona
            permission = AccessPermission.objects.filter(
                user=user,
                zone=zone,
                is_active=True,
                valid_from__lte=now.date(),
                valid_to__gte=now.date() if AccessPermission.valid_to else True,
                time_from__lte=current_time,
                time_to__gte=current_time
            ).exists()
            
            return Response({'has_permission': permission})
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except AccessZone.DoesNotExist:
            return Response(
                {'error': 'Zona no encontrada'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
    def destroy(self, request, *args, **kwargs):
        """
        Sobrescribe el método de eliminación para mejorar el manejo de errores
        """
        try:
            instance = self.get_object()
            # Registrar la eliminación para depuración
            print(f"Eliminando permiso de acceso: {instance.id} - Usuario: {instance.user.username} - Zona: {instance.zone.name}")
            
            # Realizar la eliminación
            self.perform_destroy(instance)
            
            # Registrar éxito
            print(f"Permiso de acceso eliminado correctamente: {instance.id}")
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            # Registrar el error detallado
            print(f"Error al eliminar permiso de acceso: {e}")
            # Devolver una respuesta detallada de error
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AccessLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint para consultar registros de acceso.
    """
    queryset = AccessLog.objects.all().order_by('-timestamp')
    serializer_class = AccessLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['user', 'access_point', 'status', 'direction']
    
    def get_queryset(self):
        """
        Filtrar logs según el rol del usuario:
        - Administradores y personal de seguridad: todos los logs
        - Usuarios normales: solo sus propios logs
        """
        user = self.request.user
        
        # Verificar si el usuario es administrador o personal de seguridad
        is_admin = user.is_staff or user.is_superuser
        is_security = hasattr(user, 'profile') and user.profile.role and user.profile.role.name == 'Security'
        
        if is_admin or is_security:
            return AccessLog.objects.all().order_by('-timestamp')
        else:
            return AccessLog.objects.filter(user=user).order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Obtiene los registros de acceso más recientes (últimos 10).
        """
        limit = int(request.query_params.get('limit', 10))
        logs = self.get_queryset()[:limit]
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def live_feed(self, request):
        """
        Obtiene los registros de acceso más recientes para monitoreo en tiempo real.
        """
        # Obtener el número de registros solicitados (por defecto 20)
        limit = int(request.query_params.get('limit', 20))
        
        # Filtrar por punto de acceso si se especifica
        access_point_id = request.query_params.get('access_point_id')
        queryset = self.get_queryset()
        
        if access_point_id:
            queryset = queryset.filter(access_point_id=access_point_id)
        
        # Obtener los registros más recientes
        recent_logs = queryset.order_by('-timestamp')[:limit]
        serializer = self.get_serializer(recent_logs, many=True)
        
        return Response(serializer.data)

class VisitorViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar visitantes.
    """
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['first_name', 'last_name', 'id_number', 'company', 'status']
    search_fields = ['first_name', 'last_name', 'id_number', 'company', 'email']

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        Actualiza el estado de un visitante (pending, approved, inside, outside, denied)
        """
        try:
            visitor = self.get_object()
            status_value = request.data.get('status')
            
            if status_value not in ['pending', 'approved', 'inside', 'outside', 'denied']:
                return Response(
                    {'error': 'Estado no válido. Use: pending, approved, inside, outside, denied'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Si se está cambiando a 'inside', actualizar el aforo
            if status_value == 'inside' and visitor.status != 'inside':
                occupancy = BuildingOccupancy.get_current()
                occupancy.visitors_count += 1
                occupancy.save()
            
            # Si se está cambiando de 'inside' a otro estado, actualizar el aforo
            elif visitor.status == 'inside' and status_value != 'inside':
                occupancy = BuildingOccupancy.get_current()
                if occupancy.visitors_count > 0:
                    occupancy.visitors_count -= 1
                    occupancy.save()
            
            visitor.status = status_value
            visitor.save()
            
            serializer = self.get_serializer(visitor)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, *args, **kwargs):
        """
        Sobrescribe el método update para manejar actualizaciones de estado
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Guardar el estado anterior
        old_status = instance.status
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Actualizar aforo si cambió el estado
        new_status = instance.status
        if old_status != new_status:
            occupancy = BuildingOccupancy.get_current()
            
            if new_status == 'inside' and old_status != 'inside':
                occupancy.visitors_count += 1
                occupancy.save()
            elif old_status == 'inside' and new_status != 'inside':
                if occupancy.visitors_count > 0:
                    occupancy.visitors_count -= 1
                    occupancy.save()

        # Log de actualización para depuración
        print(f"Visitante actualizado: {instance.id} - {instance.first_name} {instance.last_name} - Estado: {instance.status}")

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)
        
    def destroy(self, request, *args, **kwargs):
        """
        Sobrescribe el método de eliminación para mejorar el manejo de errores
        """
        try:
            instance = self.get_object()
            
            # No permitir eliminar si el visitante está dentro
            if instance.status == 'inside':
                return Response(
                    {'error': 'No se puede eliminar un visitante que está dentro del edificio'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Registrar la eliminación para depuración
            print(f"Eliminando visitante: {instance.id} - {instance.first_name} {instance.last_name}")
            
            # Realizar la eliminación
            self.perform_destroy(instance)
            
            # Registrar éxito
            print(f"Visitante eliminado correctamente: {instance.id}")
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            # Registrar el error detallado
            print(f"Error al eliminar visitante: {e}")
            # Devolver una respuesta detallada de error
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VisitorAccessViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar accesos de visitantes.
    """
    queryset = VisitorAccess.objects.all()
    serializer_class = VisitorAccessSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['visitor', 'host', 'is_used']
    
    def perform_create(self, serializer):
        """
        Al crear un nuevo acceso de visitante, generar el código QR
        """
        visitor = serializer.validated_data.get('visitor')
        
        # Verificar que el visitante esté aprobado
        if visitor.status != 'approved':
            raise ValidationError('El visitante debe estar aprobado para generar QR')
        
        # Generar QR único
        qr_code = str(uuid.uuid4())
        
        # Crear el acceso
        serializer.save(
            qr_code=qr_code,
            host=self.request.user if not serializer.validated_data.get('host') else serializer.validated_data.get('host')
        )
    
    @action(detail=True, methods=['get'])
    def qr_image(self, request, pk=None):
        """
        Genera y devuelve la imagen del código QR
        """
        visitor_access = self.get_object()
        
        # Crear QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Datos a codificar
        data = {
            'visitor_id': visitor_access.visitor.id,
            'qr_code': visitor_access.qr_code,
            'valid_from': visitor_access.valid_from.isoformat(),
            'valid_to': visitor_access.valid_to.isoformat()
        }
        
        qr.add_data(json.dumps(data))
        qr.make(fit=True)
        
        # Crear imagen
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a bytes
        buffer = io.BytesIO()
        img.save(buffer)
        
        # Codificar en base64 para devolver la imagen
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return Response({'qr_code_image': f"data:image/png;base64,{img_str}"})
    
    @action(detail=False, methods=['post'])
    def validate_qr(self, request):
        """
        Valida un código QR para permitir acceso a un visitante
        """
        qr_code = request.data.get('qr_code')
        access_point_id = request.data.get('access_point_id')
        
        if not qr_code or not access_point_id:
            return Response(
                {'error': 'Se requieren qr_code y access_point_id'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Intentar parsear el QR code
            try:
                qr_data = json.loads(qr_code)
                qr_code_uuid = qr_data.get('qr_code')
            except:
                # Si no es JSON, asumir que es el UUID directamente
                qr_code_uuid = qr_code
            
            # Verificar que el punto de acceso exista
            access_point = AccessPoint.objects.get(id=access_point_id)
            
            # Buscar el acceso de visitante con ese QR
            visitor_access = VisitorAccess.objects.get(qr_code=qr_code_uuid)
            
            now = timezone.now()
            
            # Verificar que el QR no haya sido usado previamente
            if visitor_access.is_used:
                return Response(
                    {'valid': False, 'reason': 'El código QR ya ha sido utilizado'}, 
                    status=status.HTTP_200_OK
                )
                
            if now < visitor_access.valid_from:
                return Response(
                    {'valid': False, 'reason': 'El acceso aún no es válido'}, 
                    status=status.HTTP_200_OK
                )
                
            if now > visitor_access.valid_to:
                return Response(
                    {'valid': False, 'reason': 'El acceso ha expirado'}, 
                    status=status.HTTP_200_OK
                )
            
            # Verificar que el visitante esté aprobado
            if visitor_access.visitor.status != 'approved':
                return Response(
                    {'valid': False, 'reason': 'El visitante no está aprobado'}, 
                    status=status.HTTP_200_OK
                )
            
            # Verificar que el punto de acceso esté en una zona permitida
            if not visitor_access.access_zones.filter(access_points=access_point).exists():
                return Response(
                    {'valid': False, 'reason': 'Punto de acceso no autorizado para este visitante'}, 
                    status=status.HTTP_200_OK
                )
            
            # Verificar aforo
            occupancy = BuildingOccupancy.get_current()
            if occupancy.total_count >= occupancy.max_capacity:
                # Registrar intento fallido
                AccessLog.objects.create(
                    access_point=access_point,
                    card_id=qr_code_uuid,
                    status=AccessLog.ACCESS_DENIED,
                    reason='Capacidad máxima alcanzada',
                    direction='in'
                )
                
                return Response(
                    {'valid': False, 'reason': 'Capacidad máxima alcanzada'}, 
                    status=status.HTTP_200_OK
                )
            
            # Acceso válido - Marcar como usado
            visitor_access.is_used = True
            visitor_access.save()
            
            # Actualizar estado del visitante a "inside"
            visitor = visitor_access.visitor
            visitor.status = 'inside'
            visitor.entry_date = now
            visitor.save()
            
            # Actualizar aforo
            occupancy.visitors_count += 1
            occupancy.save()
            
            # Registrar acceso
            AccessLog.objects.create(
                access_point=access_point,
                card_id=qr_code_uuid,
                status=AccessLog.ACCESS_GRANTED,
                reason='Acceso de visitante autorizado',
                direction='in'
            )
            
            return Response({
                'valid': True,
                'visitor': {
                    'id': visitor_access.visitor.id,
                    'name': f"{visitor_access.visitor.first_name} {visitor_access.visitor.last_name}",
                    'company': visitor_access.visitor.company,
                    'host': f"{visitor_access.host.first_name} {visitor_access.host.last_name}",
                    'purpose': visitor_access.purpose,
                    'visitor_type': visitor_access.visitor.visitor_type,
                    'apartment_number': visitor_access.visitor.apartment_number
                }
            }, status=status.HTTP_200_OK)
            
        except AccessPoint.DoesNotExist:
            return Response(
                {'valid': False, 'reason': 'Punto de acceso no encontrado'}, 
                status=status.HTTP_200_OK
            )
        except VisitorAccess.DoesNotExist:
            return Response(
                {'valid': False, 'reason': 'Código QR no válido'}, 
                status=status.HTTP_200_OK
            )
            
    def destroy(self, request, *args, **kwargs):
        """
        Sobrescribe el método de eliminación para mejorar el manejo de errores
        """
        try:
            instance = self.get_object()
            # Registrar la eliminación para depuración
            print(f"Eliminando acceso de visitante: {instance.id} - Visitante: {instance.visitor.first_name} {instance.visitor.last_name}")
            
            # Realizar la eliminación
            self.perform_destroy(instance)
            
            # Registrar éxito
            print(f"Acceso de visitante eliminado correctamente: {instance.id}")
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            # Registrar el error detallado
            print(f"Error al eliminar acceso de visitante: {e}")
            # Devolver una respuesta detallada de error
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Nuevo ViewSet para BuildingOccupancy
class BuildingOccupancyViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar el aforo del edificio.
    """
    queryset = BuildingOccupancy.objects.all()
    serializer_class = BuildingOccupancySerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        Obtiene el aforo actual del edificio.
        """
        occupancy = BuildingOccupancy.get_current()
        serializer = self.get_serializer(occupancy)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def update_residents(self, request):
        """
        Actualiza el conteo de residentes.
        """
        residents_count = request.data.get('residents_count')
        
        if residents_count is None:
            return Response(
                {'error': 'Se requiere residents_count'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            residents_count = int(residents_count)
            if residents_count < 0:
                raise ValueError("El conteo no puede ser negativo")
            
            occupancy = BuildingOccupancy.get_current()
            occupancy.residents_count = residents_count
            occupancy.save()
            
            serializer = self.get_serializer(occupancy)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )