#!/usr/bin/env bash

set -o errexit  # exit on error

uname -a
pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py makemigrations strava2
python manage.py migrate
