#!/usr/bin/env bash

set -o errexit  # exit on error

pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --no-input
echo "static ..."
ls -1 /opt/render/project/src/MyRuns/static
ln -s /opt/render/project/src/MyRuns/static /opt/render/project/src/static
python manage.py migrate
