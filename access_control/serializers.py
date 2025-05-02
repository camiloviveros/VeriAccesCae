from rest_framework import serializers
from django.utils import timezone
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

class AccessPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessPoint
        fields = '__all__'

class AccessZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessZone
        fields = '__all__'

class AccessCardSerializer(serializers.ModelSerializer):
    user_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = AccessCard
        fields = ['id', 'card_id', 'user', 'user_detail', 'is_active', 'issue_date', 'expiry_date']
    
    def get_user_detail(self, obj):
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'full_name': f"{obj.user.first_name} {obj.user.last_name}".strip()
            }
        return None

class AccessPermissionSerializer(serializers.ModelSerializer):
    user_detail = serializers.SerializerMethodField()
    zone_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = AccessPermission
        fields = ['id', 'user', 'user_detail', 'zone', 'zone_detail', 'time_from', 'time_to', 
                  'valid_from', 'valid_to', 'is_active']
    
    def get_user_detail(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'full_name': f"{obj.user.first_name} {obj.user.last_name}".strip()
        }
    
    def get_zone_detail(self, obj):
        return {
            'id': obj.zone.id,
            'name': obj.zone.name
        }
        
    def validate(self, data):
        """
        Validar que la fecha de inicio sea anterior a la de fin
        """
        if 'valid_from' in data and 'valid_to' in data and data['valid_from'] > data['valid_to']:
            raise serializers.ValidationError("La fecha de inicio debe ser anterior a la de fin")
        
        if 'time_from' in data and 'time_to' in data and data['time_from'] > data['time_to']:
            raise serializers.ValidationError("La hora de inicio debe ser anterior a la de fin")
        
        return data

class AccessLogSerializer(serializers.ModelSerializer):
    user_detail = serializers.SerializerMethodField()
    access_point_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = AccessLog
        fields = ['id', 'user', 'user_detail', 'access_point', 'access_point_detail', 'card_id',
                  'timestamp', 'status', 'reason', 'direction']
    
    def get_user_detail(self, obj):
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'full_name': f"{obj.user.first_name} {obj.user.last_name}".strip()
            }
        return None
    
    def get_access_point_detail(self, obj):
        return {
            'id': obj.access_point.id,
            'name': obj.access_point.name,
            'location': obj.access_point.location
        }

class VisitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = ['id', 'first_name', 'last_name', 'id_number', 'phone', 'email', 
                 'company', 'photo', 'created_at', 'status', 'visitor_type', 
                 'apartment_number', 'entry_date', 'exit_date']

class VisitorAccessSerializer(serializers.ModelSerializer):
    visitor_detail = serializers.SerializerMethodField()
    host_detail = serializers.SerializerMethodField()
    access_zones_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = VisitorAccess
        fields = ['id', 'visitor', 'visitor_detail', 'host', 'host_detail', 'purpose', 
                  'valid_from', 'valid_to', 'access_zones', 'access_zones_detail', 
                  'qr_code', 'is_used', 'created_at']
        read_only_fields = ['qr_code', 'is_used', 'created_at']
    
    def get_visitor_detail(self, obj):
        return {
            'id': obj.visitor.id,
            'name': f"{obj.visitor.first_name} {obj.visitor.last_name}",
            'id_number': obj.visitor.id_number,
            'company': obj.visitor.company
        }
    
    def get_host_detail(self, obj):
        return {
            'id': obj.host.id,
            'username': obj.host.username,
            'full_name': f"{obj.host.first_name} {obj.host.last_name}".strip()
        }
    
    def get_access_zones_detail(self, obj):
        return [{'id': zone.id, 'name': zone.name} for zone in obj.access_zones.all()]
        
    def validate(self, data):
        """
        Validar que la fecha de inicio sea anterior a la de fin
        """
        if data['valid_from'] >= data['valid_to']:
            raise serializers.ValidationError("La fecha/hora de inicio debe ser anterior a la de fin")
        
        # Validar que la fecha de fin no sea demasiado lejana (máximo 30 días)
        max_days = 30
        if (data['valid_to'] - data['valid_from']).days > max_days:
            raise serializers.ValidationError(f"El acceso no puede ser válido por más de {max_days} días")
        
        return data