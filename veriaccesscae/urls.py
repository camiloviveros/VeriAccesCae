from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuración de Swagger/OpenAPI
schema_view = get_schema_view(
   openapi.Info(
      title="VeriAccessSCAE API",
      default_version='v1',
      description="API para el Sistema de Control de Acceso para Edificios",
      terms_of_service="https://www.example.com/terms/",
      contact=openapi.Contact(email="contact@example.com"),
      license=openapi.License(name="Licencia Privada"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin de Django
    path('admin/', admin.site.urls),
    
    # Documentación API con Swagger
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # APIs por módulo
    path('api/auth/', include('authentication.urls')),
    path('api/access/', include('access_control.urls')),
    path('api/parking/', include('parking.urls')),
    path('api/security/', include('security.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/reports/', include('reporting.urls')),
]

# Servir archivos media en modo desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)