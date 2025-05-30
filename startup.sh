#!/bin/bash

# Script de inicio para Azure App Service

# Establecer variables de entorno
export DJANGO_SETTINGS_MODULE=veriaccesscae.settings_sqlite

# Ejecutar migraciones
echo "Ejecutando migraciones..."
python manage.py migrate --no-input

# Cargar datos iniciales si no existen
echo "Verificando datos iniciales..."
python manage.py loaddata initial_data.json --verbosity 0 || true

# Crear superusuario si no existe
echo "Verificando superusuario..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@veriaccess.com', 'admin123456')
    print('Superusuario creado')
"

# Iniciar Gunicorn
echo "Iniciando Gunicorn..."
gunicorn --bind=0.0.0.0:8000 --workers=4 --timeout=600 veriaccesscae.wsgi:application