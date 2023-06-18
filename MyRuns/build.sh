#!/usr/bin/env bash

set -o errexit  # exit on error

uname -a
pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py makemigrations strava2
python manage.py migrate 

#python manage.py shell << FF
#from django.contrib.auth import get_user_model
#User = get_user_model()
#User.objects.create_superuser('admin', 'email', 'password')
#exit()
#FF
