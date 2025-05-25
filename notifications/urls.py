from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.permissions import IsAuthenticated

# Creación de vistas simples para los modelos de notifications
from rest_framework import viewsets
from .models import NotificationTemplate, Notification, NotificationPreference
from rest_framework import serializers

# Serializers
class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = '__all__'

# ViewSets
class NotificationTemplateViewSet(viewsets.ModelViewSet):
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAuthenticated]

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Los usuarios normales solo ven sus propias notificaciones
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Notification.objects.all().order_by('-created_at')
        return Notification.objects.filter(recipient=self.request.user)

class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Los usuarios solo pueden ver/editar sus propias preferencias
        return NotificationPreference.objects.filter(user=self.request.user)

# Router
router = DefaultRouter()
router.register(r'templates', NotificationTemplateViewSet)
router.register(r'messages', NotificationViewSet, basename='notification')
router.register(r'preferences', NotificationPreferenceViewSet, basename='preference')

urlpatterns = [
    path('', include(router.urls)),
]