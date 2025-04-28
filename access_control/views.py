from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
import datetime
import uuid

from authentication.models import User
from .models import (
    AccessPoint, 
    AccessZone, 
    AccessCard, 
    AccessPermission, 
    AccessLog, 
    Visitor, 
    VisitorAccess
)
from .serializers import (
    AccessPointSerializer,
    AccessZoneSerializer,
    AccessCardSerializer,
    AccessPermissionSerializer,
    AccessLogSerializer,
    VisitorSerializer,
    VisitorAccessSerializer
)
from .permissions import IsSecurityPersonnel, IsReceptionist, IsAdministrator
from django.shortcuts import get_object_or_404
import qrcode
import io
import base64
from django.core.files.base import ContentFile

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
    filterset_fields = ['first_name', 'last_name', 'id_number', 'company']
    search_fields = ['first_name', 'last_name', 'id_number', 'company', 'email']

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
        # Generar un identificador único para el QR
        qr_code = str(uuid.uuid4())
        
        # Guardar con el QR code
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
        
        # Datos a codificar (incluir información del acceso)
        data = {
            'type': 'visitor_access',
            'id': visitor_access.id,
            'qr_code': visitor_access.qr_code,
            'visitor_id': visitor_access.visitor.id,
            'valid_from': visitor_access.valid_from.isoformat(),
            'valid_to': visitor_access.valid_to.isoformat()
        }
        
        qr.add_data(str(data))
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
            # Verificar que el punto de acceso exista
            access_point = AccessPoint.objects.get(id=access_point_id)
            
            # Buscar el acceso de visitante con ese QR
            visitor_access = VisitorAccess.objects.get(qr_code=qr_code)
            
            now = timezone.now()
            
            # Verificar validez
            if visitor_access.is_used:
                return Response(
                    {'valid': False, 'reason': 'El código QR ya ha sido utilizado'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if now < visitor_access.valid_from:
                return Response(
                    {'valid': False, 'reason': 'El acceso aún no es válido'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if now > visitor_access.valid_to:
                return Response(
                    {'valid': False, 'reason': 'El acceso ha expirado'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar que el punto de acceso esté en una zona permitida
            if not visitor_access.access_zones.filter(access_points=access_point).exists():
                return Response(
                    {'valid': False, 'reason': 'Punto de acceso no autorizado para este visitante'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar aforo si es necesario
            if access_point.max_capacity > 0 and access_point.current_count >= access_point.max_capacity:
                # Registrar intento fallido
                AccessLog.objects.create(
                    access_point=access_point,
                    card_id=qr_code,
                    status=AccessLog.ACCESS_DENIED,
                    reason='Capacidad máxima alcanzada',
                    direction='in'
                )
                
                return Response(
                    {'valid': False, 'reason': 'Capacidad máxima alcanzada'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Acceso válido - Marcar como usado para evitar re-uso
            visitor_access.is_used = True
            visitor_access.save()
            
            # Registrar acceso
            AccessLog.objects.create(
                access_point=access_point,
                card_id=qr_code,
                status=AccessLog.ACCESS_GRANTED,
                reason='Acceso de visitante autorizado',
                direction='in'
            )
            
            # Actualizar contadores de aforo
            access_point.current_count += 1
            access_point.save()
            
            for zone in visitor_access.access_zones.all():
                if zone.access_points.filter(id=access_point.id).exists():
                    zone.current_count += 1
                    zone.save()
            
            return Response({
                'valid': True,
                'visitor': {
                    'id': visitor_access.visitor.id,
                    'name': f"{visitor_access.visitor.first_name} {visitor_access.visitor.last_name}",
                    'company': visitor_access.visitor.company,
                    'host': f"{visitor_access.host.first_name} {visitor_access.host.last_name}",
                    'purpose': visitor_access.purpose
                }
            })
            
        except AccessPoint.DoesNotExist:
            return Response(
                {'error': 'Punto de acceso no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except VisitorAccess.DoesNotExist:
            return Response(
                {'valid': False, 'reason': 'Código QR no válido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )