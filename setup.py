#!/usr/bin/env python
"""
Script para inicializar el proyecto VeriAccessSCAE.
Crea la estructura de directorios y archivos básicos.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

# Directorios y archivos a crear
PROJECT_NAME = 'veriaccesscae'
APPS = [
    'authentication',
    'access_control',
    'parking',
    'security',
    'notifications',
    'reporting',
    'common',
]

def create_django_project():
    """Crear proyecto Django base"""
    try:
        # Verificar si Django está instalado
        subprocess.run(
            [sys.executable, '-m', 'django', '--version'],
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError:
        print("Django no está instalado. Instalando...")
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'django'],
            check=True
        )
    
    # Crear proyecto
    if not os.path.exists(PROJECT_NAME):
        print(f"Creando proyecto Django '{PROJECT_NAME}'...")
        subprocess.run(
            [sys.executable, '-m', 'django', 'startproject', PROJECT_NAME, '.'],
            check=True
        )
    else:
        print(f"Proyecto '{PROJECT_NAME}' ya existe.")

def create_apps():
    """Crear las aplicaciones Django"""
    for app in APPS:
        if not os.path.exists(app):
            print(f"Creando aplicación '{app}'...")
            subprocess.run(
                [sys.executable, 'manage.py', 'startapp', app],
                check=True
            )
        else:
            print(f"Aplicación '{app}' ya existe.")

def create_directory_structure():
    """Crear estructura adicional de directorios"""
    # Crear directorios para media y static
    os.makedirs('media', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Crear directorios para migraciones
    for app in APPS:
        migrations_dir = os.path.join(app, 'migrations')
        os.makedirs(migrations_dir, exist_ok=True)
        # Crear archivo __init__.py en migrations
        init_file = os.path.join(migrations_dir, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('# Migrations directory\n')

def create_requirements_file():
    """Crear archivo requirements.txt"""
    requirements = """Django==4.2.8
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.0
psycopg2-binary==2.9.9
pillow==10.1.0
django-cors-headers==4.3.0
drf-yasg==1.21.7
django-filter==23.4
celery==5.3.4
redis==5.0.1
reportlab==4.0.7
openpyxl==3.1.2
python-dotenv==1.0.0
gunicorn==21.2.0
django-storages==1.14.2
qrcode==7.4.2
"""
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    print("Archivo requirements.txt creado.")

def main():
    """Función principal"""
    print("Iniciando configuración del proyecto VeriAccessSCAE...")
    
    # Crear proyecto y apps
    create_django_project()
    create_apps()
    create_directory_structure()
    create_requirements_file()
    
    print("\nInstalando dependencias...")
    subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
        check=True
    )
    
    print("\nConfiguración completada con éxito!")
    print("\nPróximos pasos:")
    print("1. Configurar la base de datos PostgreSQL en veriaccesscae/settings.py")
    print("2. Ejecutar migraciones: python manage.py makemigrations")
    print("3. Aplicar migraciones: python manage.py migrate")
    print("4. Crear superusuario: python manage.py createsuperuser")
    print("5. Cargar datos iniciales: python manage.py loaddata initial_data.json")
    print("6. Iniciar servidor: python manage.py runserver")

if __name__ == "__main__":
    main()