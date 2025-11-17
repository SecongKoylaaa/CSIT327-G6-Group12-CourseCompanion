#!/usr/bin/env bash
set -euo pipefail

echo "==> Installing dependencies"
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Running database migrations"
python backend/manage.py makemigrations
python backend/manage.py migrate --noinput

echo "==> Collecting static files"
python backend/manage.py collectstatic --noinput

echo "==> Build complete"
