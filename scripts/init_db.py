#!/usr/bin/env python
"""
Script para inicializar la base de datos PostgreSQL para el proyecto VeriAccessSCAE.
Este script crea la base de datos y el usuario si no existen.
"""
import os
import sys
import argparse
import subprocess
import getpass

def run_psql_command(command, dbname="postgres", username=None, password=None):
    """Ejecutar comandos SQL en PostgreSQL"""
    psql_command = ["psql"]
    
    if username:
        psql_command.extend(["-U", username])
    
    psql_command.extend(["-d", dbname, "-c", command])
    
    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password
    
    try:
        result = subprocess.run(
            psql_command,
            check=True,
            capture_output=True,
            text=True,
            env=env
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando comando SQL: {e}")
        print(f"Salida de error: {e.stderr}")
        return None

def database_exists(dbname, username=None, password=None):
    """Verificar si la base de datos existe"""
    command = f"SELECT 1 FROM pg_database WHERE datname = '{dbname}';"
    result = run_psql_command(command, username=username, password=password)
    return result and "(1 row)" in result

def user_exists(username, admin_username=None, admin_password=None):
    """Verificar si el usuario de PostgreSQL existe"""
    command = f"SELECT 1 FROM pg_roles WHERE rolname = '{username}';"
    result = run_psql_command(command, username=admin_username, password=admin_password)
    return result and "(1 row)" in result

def create_database(dbname, username, password, admin_username=None, admin_password=None):
    """Crear base de datos y usuario"""
    # Crear usuario si no existe
    if not user_exists(username, admin_username, admin_password):
        print(f"Creando usuario PostgreSQL '{username}'...")
        run_psql_command(
            f"CREATE USER {username} WITH PASSWORD '{password}';",
            username=admin_username,
            password=admin_password
        )
        print(f"Usuario '{username}' creado exitosamente.")
    else:
        print(f"Usuario '{username}' ya existe.")
    
    # Crear base de datos si no existe
    if not database_exists(dbname, admin_username, admin_password):
        print(f"Creando base de datos '{dbname}'...")
        run_psql_command(
            f"CREATE DATABASE {dbname};",
            username=admin_username,
            password=admin_password
        )
        print(f"Base de datos '{dbname}' creada exitosamente.")
    else:
        print(f"Base de datos '{dbname}' ya existe.")
    
    # Asignar permisos
    print("Configurando permisos...")
    run_psql_command(
        f"ALTER ROLE {username} SET client_encoding TO 'utf8';",
        username=admin_username,
        password=admin_password
    )
    run_psql_command(
        f"ALTER ROLE {username} SET default_transaction_isolation TO 'read committed';",
        username=admin_username,
        password=admin_password
    )
    run_psql_command(
        f"ALTER ROLE {username} SET timezone TO 'UTC';",
        username=admin_username,
        password=admin_password
    )
    run_psql_command(
        f"GRANT ALL PRIVILEGES ON DATABASE {dbname} TO {username};",
        username=admin_username,
        password=admin_password
    )
    print("Permisos configurados correctamente.")

def update_django_settings(dbname, username, password, host="localhost", port="5432"):
    """Actualizar el archivo settings.py con la configuración de la base de datos"""
    settings_path = os.path.join("veriaccesscae", "settings.py")
    
    if not os.path.exists(settings_path):
        print(f"Error: No se encontró el archivo {settings_path}")
        return False
    
    with open(settings_path, "r") as f:
        settings_content = f.read()
    
    # Buscar la configuración existente de la base de datos
    db_config_start = settings_content.find("DATABASES = {")
    if db_config_start == -1:
        print("Error: No se encontró la configuración DATABASES en settings.py")
        return False
    
    # Encontrar dónde termina la configuración de la base de datos
    db_config_end = settings_content.find("}", db_config_start)
    db_config_end = settings_content.find("}", db_config_end + 1) + 1
    
    # Nueva configuración de la base de datos
    new_db_config = f"""DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': '{dbname}',
        'USER': '{username}',
        'PASSWORD': '{password}',
        'HOST': '{host}',
        'PORT': '{port}',
    }}
}}"""
    
    # Reemplazar la configuración existente
    new_settings_content = settings_content[:db_config_start] + new_db_config + settings_content[db_config_end:]
    
    # Guardar los cambios
    with open(settings_path, "w") as f:
        f.write(new_settings_content)
    
    print(f"Archivo {settings_path} actualizado con la configuración de PostgreSQL.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Inicializar base de datos PostgreSQL para VeriAccessSCAE")
    parser.add_argument("--dbname", default="veriaccesscae_db", help="Nombre de la base de datos")
    parser.add_argument("--dbuser", default="postgres_user", help="Usuario de la base de datos")
    parser.add_argument("--dbpass", help="Contraseña del usuario de la base de datos")
    parser.add_argument("--dbhost", default="localhost", help="Host de la base de datos")
    parser.add_argument("--dbport", default="5432", help="Puerto de la base de datos")
    parser.add_argument("--pguser", help="Usuario administrador de PostgreSQL")
    parser.add_argument("--pgpass", help="Contraseña del usuario administrador de PostgreSQL")
    
    args = parser.parse_args()
    
    # Solicitar contraseñas si no se proporcionaron
    if not args.dbpass:
        args.dbpass = getpass.getpass(f"Contraseña para el usuario '{args.dbuser}': ")
    
    if not args.pguser:
        args.pguser = input("Usuario administrador de PostgreSQL [postgres]: ") or "postgres"
    
    if not args.pgpass:
        args.pgpass = getpass.getpass(f"Contraseña para el usuario '{args.pguser}': ")
    
    print("=== Inicialización de la base de datos PostgreSQL para VeriAccessSCAE ===")
    
    # Crear base de datos y usuario
    create_database(args.dbname, args.dbuser, args.dbpass, args.pguser, args.pgpass)
    
    # Actualizar settings.py
    if update_django_settings(args.dbname, args.dbuser, args.dbpass, args.dbhost, args.dbport):
        print("\nConfiguración de la base de datos completada con éxito!")
        print("\nPróximos pasos:")
        print("1. Ejecutar migraciones: python manage.py makemigrations")
        print("2. Aplicar migraciones: python manage.py migrate")
        print("3. Cargar datos iniciales: python manage.py loaddata initial_data.json")

if __name__ == "__main__":
    main()