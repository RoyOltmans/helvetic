#!/usr/bin/env bash

# entrypoint.sh — run pending Django migrations, then start Gunicorn

set -e

# Collect static files (if used)
# python manage.py collectstatic --noinput

# Install Python dependencies on container start
pip install --no-cache-dir -r requirements.txt
pip install --no-cache-dir "Django==1.9.0" "gunicorn==19.9.0"

# Apply Django migrations (optional)
python /app/helv_test/manage.py migrate --noinput || true

# Start Gunicorn
exec "$@"

# Launch Gunicorn
exec gunicorn \
  --chdir /app/helvetic/helv_test \
  helv_test.wsgi:application \
  --bind 0.0.0.0:5000 \
  --workers 3
