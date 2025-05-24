
from django.db import migrations
from django.utils import timezone


def assign_default_parking_area(apps, schema_editor):
    """Asignar área por defecto a vehículos existentes"""
    Vehicle = apps.get_model('parking', 'Vehicle')
    ParkingArea = apps.get_model('parking', 'ParkingArea')
    ParkingAccess = apps.get_model('parking', 'ParkingAccess')
    
    # Crear área por defecto si no existe
    default_area, created = ParkingArea.objects.get_or_create(
        name='Área General',
        defaults={
            'description': 'Área creada automáticamente para vehículos existentes',
            'max_capacity': 100,
            'current_count': 0,
            'is_active': True
        }
    )
    
    # Obtener vehículos sin área asignada
    vehicles_without_area = Vehicle.objects.filter(parking_area__isnull=True)
    count = vehicles_without_area.count()
    
    if count > 0:
        # Asignar área por defecto
        for vehicle in vehicles_without_area:
            vehicle.parking_area = default_area
            vehicle.save()
        
        # Actualizar contador
        default_area.current_count = count
        default_area.save()
        
        # Crear accesos automáticos
        for vehicle in vehicles_without_area:
            ParkingAccess.objects.get_or_create(
                vehicle=vehicle,
                parking_area=default_area,
                defaults={'valid_from': timezone.now().date()}
            )


def reverse_assignment(apps, schema_editor):
    """Reversar la asignación"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('parking', '0002_add_parking_area_nullable'),
    ]

    operations = [
        migrations.RunPython(assign_default_parking_area, reverse_assignment),
    ]