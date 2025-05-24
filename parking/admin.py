from django.contrib import admin
from .models import ParkingArea, Vehicle, ParkingAccess, ParkingLog


@admin.register(ParkingArea)
class ParkingAreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'max_capacity', 'current_count', 'available_spots', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['current_count']
    
    def available_spots(self, obj):
        return obj.max_capacity - obj.current_count
    available_spots.short_description = 'Espacios Disponibles'


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['license_plate', 'user', 'brand', 'model', 'color', 'parking_area', 'is_active', 'created_at']
    list_filter = ['is_active', 'brand', 'parking_area', 'created_at']
    search_fields = ['license_plate', 'brand', 'model', 'user__username']
    readonly_fields = ['user', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(ParkingAccess)
class ParkingAccessAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'parking_area', 'valid_from', 'valid_to', 'is_active']
    list_filter = ['parking_area', 'valid_from']
    search_fields = ['vehicle__license_plate', 'parking_area__name']
    
    def is_active(self, obj):
        from django.utils import timezone
        today = timezone.now().date()
        return obj.valid_from <= today and (obj.valid_to is None or obj.valid_to >= today)
    is_active.boolean = True
    is_active.short_description = 'Activo'


@admin.register(ParkingLog)
class ParkingLogAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'parking_area', 'timestamp', 'direction', 'status', 'reason']
    list_filter = ['direction', 'status', 'timestamp', 'parking_area']
    search_fields = ['vehicle__license_plate', 'parking_area__name', 'reason']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'