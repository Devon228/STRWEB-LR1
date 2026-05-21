#!/bin/sh
set -e

echo "Waiting for database..."
python << 'PY'
import os
import sys
import time

url = os.environ.get("DATABASE_URL", "")
if not url:
    sys.exit(0)

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PharmacyProject.settings")
django.setup()
from django.db import connection

for attempt in range(30):
    try:
        connection.ensure_connection()
        print("Database is ready.")
        break
    except Exception as exc:
        print(f"DB not ready ({attempt + 1}/30): {exc}")
        time.sleep(2)
else:
    print("Database connection failed.")
    sys.exit(1)
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn PharmacyProject.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile -
