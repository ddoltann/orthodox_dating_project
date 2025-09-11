#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate

pip install gunicorn uvicorn

pip freeze > requirements.txt
