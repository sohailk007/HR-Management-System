#!/bin/bash

# Wait for the database to be ready
echo "Waiting for database..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $POSTGRES_USER; do
  sleep 1
done
echo "Database ready!"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files in production
if [ "$DJANGO_DEBUG" = "False" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

# Start the application
if [ "$DJANGO_DEBUG" = "True" ]; then
  echo "Starting Django development server..."
  exec python manage.py runserver 0.0.0.0:7000
else
  echo "Starting Gunicorn production server..."
  exec gunicorn HRMs.wsgi:application \
      --bind 0.0.0.0:7000 \
      --workers 3 \
      --timeout 120 \
      --log-level info
fi
