from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate

from .models import User, Role, Permission, RolePermission, UserProfile

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255, required=True)
    password = serializers.CharField(max_length=128, required=True, write_only=True)

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        request = self.context.get('request')
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # Verificar contraseña actual
        if not request.user.check_password(current_password):
            raise serializers.ValidationError({'current_password': 'La contraseña actual es incorrecta'})
        
        # Verificar que las contraseñas nuevas coincidan
        if new_password != confirm_password:
            raise serializers.ValidationError({'confirm_password': 'Las contraseñas no coinciden'})
        
        # Validar política de contraseñas
        try:
            validate_password(new_password, request.user)
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': list(e)})
        
        return data

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'code', 'description']

class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'created_at']

class UserProfileSerializer(serializers.ModelSerializer):
    role_detail = RoleSerializer(source='role', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'role', 'role_detail', 'department', 'employee_id', 'photo']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    role_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'first_name', 'last_name',
            'phone', 'is_active', 'is_staff', 'date_joined', 'profile', 
            'role_id', 'is_locked', 'login_attempts'
        ]
        read_only_fields = ['date_joined', 'is_locked', 'login_attempts']
    
    def create(self, validated_data):
        role_id = validated_data.pop('role_id', None)
        password = validated_data.pop('password', None)
        
        user = User.objects.create(**validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        # Crear perfil de usuario
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Asignar rol si se proporciona
        if role_id:
            try:
                role = Role.objects.get(id=role_id)
                profile.role = role
                profile.save()
            except Role.DoesNotExist:
                pass
        
        return user
    
    def update(self, instance, validated_data):
        role_id = validated_data.pop('role_id', None)
        password = validated_data.pop('password', None)
        
        # Actualizar campos del usuario
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Actualizar contraseña si se proporciona
        if password:
            instance.set_password(password)
        
        instance.save()
        
        # Actualizar perfil y rol
        profile, created = UserProfile.objects.get_or_create(user=instance)
        
        if role_id:
            try:
                role = Role.objects.get(id=role_id)
                profile.role = role
                profile.save()
            except Role.DoesNotExist:
                pass
        
        return instance