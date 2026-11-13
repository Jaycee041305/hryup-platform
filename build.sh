#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate || echo "Warning: Database migration failed or database unreachable. Continuing deployment..."

