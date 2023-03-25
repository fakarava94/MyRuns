#!/usr/bin/env bash

set -o errexit  # exit on error

pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --no-input
echo "static ..."
ls -1 MyRuns/static
python manage.py migrate
