#!/usr/bin/env bash
set -euo pipefail

# Add backend folder to PYTHONPATH so Django modules are found
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/backend"

echo "==> Installing dependencies"
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Running database migrations"
python backend/manage.py makemigrations
python backend/manage.py migrate --noinput

echo "==> Collecting static files"
python backend/manage.py collectstatic --noinput

echo "==> Build complete"
