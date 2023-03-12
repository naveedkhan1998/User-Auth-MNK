#!/bin/sh
python3 manage.py wait_for_db
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py initadmin
gunicorn backend.wsgi:application --bind 0.0.0.0:8000 -w 4