#!/bin/sh
set -e

python manage.py collectstatic --noinput
python manage.py migrate --noinput

gunicorn foodgram_backend.wsgi:application --bind 0.0.0.0:8000
