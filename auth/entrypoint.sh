#!/bin/bash

python manage.py makemigrations users

python manage.py migrate --fake users 0001_initial

python manage.py migrate 

exec uvicorn auth_service.asgi:application --host 0.0.0.0 --port 8000