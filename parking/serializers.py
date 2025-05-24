from rest_framework import serializers
from django.db.models import Q, Count, F
from .models import ParkingArea, Vehicle, ParkingAccess, ParkingLog


class ParkingAreaSerializer(serializers.ModelSerializer):
    available_spots = serializers.SerializerMethodField()
    
    class Meta:
        model = ParkingArea
        fields = '__all__'
        
    def get_available_spots(self, obj):
        return obj.max_capacity - obj.current_count


class VehicleSerializer(serializers.ModelSerializer):
    user_detail = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Vehicle
        fields = '__all__'
        read_only_fields = ['user']  # El user se asigna automáticamente
        
    def get_user_detail(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name
        }
        
    def validate_license_plate(self, value):
        """Validar que la placa sea única para el usuario"""
        user = self.context['request'].user
        existing = Vehicle.objects.filter(
            user=user, 
            license_plate=value
        ).exclude(pk=self.instance.pk if self.instance else None)
        
        if existing.exists():
            raise serializers.ValidationError(
                "Ya tienes un vehículo registrado con esta placa."
            )
        return value.upper()  # Convertir a mayúsculas


class ParkingAccessSerializer(serializers.ModelSerializer):
    vehicle_detail = VehicleSerializer(source='vehicle', read_only=True)
    parking_area_detail = ParkingAreaSerializer(source='parking_area', read_only=True)
    
    class Meta:
        model = ParkingAccess
        fields = '__all__'
        
    def validate(self, data):
        """Validar que el vehículo pertenezca al usuario actual"""
        if 'vehicle' in data:
            user = self.context['request'].user
            if not user.is_staff and data['vehicle'].user != user:
                raise serializers.ValidationError(
                    "No puedes crear acceso para vehículos de otros usuarios."
                )
        return data


class ParkingLogSerializer(serializers.ModelSerializer):
    vehicle_detail = VehicleSerializer(source='vehicle', read_only=True)
    parking_area_detail = ParkingAreaSerializer(source='parking_area', read_only=True)
    
    class Meta:
        model = ParkingLog
        fields = '__all__'
        read_only_fields = ['timestamp']