#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Instalar librerías
pip install -r requirements.txt

# 2. Recolectar archivos estáticos (CSS del admin, imágenes)
python manage.py collectstatic --no-input

# 3. Aplicar migraciones a la Base de Datos de la nube
python manage.py migrate