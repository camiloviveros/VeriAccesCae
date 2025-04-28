from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.permissions import IsAuthenticated

# Creación de vistas simples para los modelos de parking
from rest_framework import viewsets
from .models import ParkingArea, Vehicle, ParkingAccess, ParkingLog
from rest_framework import serializers

# Serializers
class ParkingAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingArea
        fields = '__all__'

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'

class ParkingAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingAccess
        fields = '__all__'

class ParkingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingLog
        fields = '__all__'

# ViewSets
class ParkingAreaViewSet(viewsets.ModelViewSet):
    queryset = ParkingArea.objects.all()
    serializer_class = ParkingAreaSerializer
    permission_classes = [IsAuthenticated]

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filtrar vehículos por usuario si no es admin
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Vehicle.objects.all()
        return Vehicle.objects.filter(user=user)

class ParkingAccessViewSet(viewsets.ModelViewSet):
    queryset = ParkingAccess.objects.all()
    serializer_class = ParkingAccessSerializer
    permission_classes = [IsAuthenticated]

class ParkingLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ParkingLog.objects.all()
    serializer_class = ParkingLogSerializer
    permission_classes = [IsAuthenticated]

# Router
router = DefaultRouter()
router.register(r'areas', ParkingAreaViewSet)
router.register(r'vehicles', VehicleViewSet)
router.register(r'access', ParkingAccessViewSet)
router.register(r'logs', ParkingLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]