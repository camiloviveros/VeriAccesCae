from django.contrib.auth import authenticate
from rest_framework import status, viewsets, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.utils import timezone

from .models import User, Role, Permission, RolePermission, UserProfile
from .serializers import (
    UserSerializer, 
    UserProfileSerializer, 
    RoleSerializer, 
    PermissionSerializer,
    LoginSerializer,
    ChangePasswordSerializer
)

class LoginView(APIView):
    """
    API endpoint para iniciar sesión y obtener tokens JWT.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        
        if not user:
            try:
                user_obj = User.objects.get(username=username)
                user_obj.record_login_attempt(success=False)
                
                if user_obj.is_locked:
                    return Response(
                        {'error': 'La cuenta ha sido bloqueada por múltiples intentos fallidos'}, 
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                
                return Response(
                    {'error': 'Credenciales inválidas'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            except User.DoesNotExist:
                return Response(
                    {'error': 'Credenciales inválidas'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        if user.is_locked:
            return Response(
                {'error': 'La cuenta está bloqueada. Contacte al administrador'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Acceso exitoso, resetear intentos de login
        user.record_login_attempt(success=True)
        user.last_login = timezone.now()
        user.save()
        
        refresh = RefreshToken.for_user(user)
        
        # Incluir información básica del usuario y su rol
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }
        
        # Incluir información del rol si está disponible
        try:
            profile = user.profile
            if profile and profile.role:
                user_data['role'] = {
                    'id': profile.role.id,
                    'name': profile.role.name
                }
        except UserProfile.DoesNotExist:
            pass
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_data
        })

class LogoutView(APIView):
    """
    API endpoint para cerrar sesión.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # En un sistema JWT real, registraríamos el token en una lista negra
            return Response({"detail": "Sesión cerrada exitosamente"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    """
    API endpoint para cambiar la contraseña.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"detail": "Contraseña actualizada correctamente"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint para listar, crear y actualizar usuarios.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]  # Solo administradores pueden gestionar usuarios
    filterset_fields = ['username', 'email', 'is_active', 'profile__role']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def perform_create(self, serializer):
        user = serializer.save()
        # Crear perfil si no existe
        UserProfile.objects.get_or_create(user=user)

class CurrentUserView(APIView):
    """
    API endpoint para obtener o actualizar el usuario actual.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    def patch(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RoleViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar roles.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdminUser]

class PermissionViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar permisos.
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAdminUser]

class RegisterView(APIView):
    """
    API endpoint para registro de nuevos usuarios.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Crear perfil de usuario si no existe
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Asignar rol de "Usuario" común
            try:
                # Buscar el rol de "Usuario" para usuarios normales
                regular_role = Role.objects.get(name='Usuario')
                profile.role = regular_role
                profile.save()
            except Role.DoesNotExist:
                # Si no existe el rol "Usuario", crearlo
                regular_role = Role.objects.create(
                    name='Usuario',
                    description='Usuario regular del sistema con acceso básico'
                )
                profile.role = regular_role
                profile.save()
            
            # Generar tokens para logeo automático después del registro
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'detail': 'Usuario registrado correctamente',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': {
                        'id': regular_role.id,
                        'name': regular_role.name
                    }
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def head(self, request):
        # Para peticiones HEAD simplemente devuelve una respuesta exitosa sin cuerpo
        return Response(status=status.HTTP_200_OK)

class CreateAdminUserView(APIView):
    """
    API endpoint para crear usuarios administrativos.
    Solo puede ser usado por superusuarios.
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        # Verificar que el usuario que hace la solicitud es superusuario
        if not request.user.is_superuser:
            return Response(
                {'error': 'Solo los superusuarios pueden crear usuarios administrativos'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Crear perfil de usuario si no existe
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Asignar rol "Administrativo"
            try:
                admin_role = Role.objects.get(name='Administrativo')
            except Role.DoesNotExist:
                # Si no existe el rol "Administrativo", crearlo
                admin_role = Role.objects.create(
                    name='Administrativo',
                    description='Usuario administrativo con acceso al panel de control'
                )
            
            profile.role = admin_role
            profile.save()
            
            return Response({
                'detail': 'Usuario administrativo creado correctamente',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': {
                        'id': admin_role.id,
                        'name': admin_role.name
                    }
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)