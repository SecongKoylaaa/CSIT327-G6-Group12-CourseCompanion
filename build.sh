#!/usr/bin/env bash
set -euo pipefail

# Add backend folder to PYTHONPATH so Django modules are found
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/backend"

echo "==> Installing dependencies"
pip install --upgrade pip
pip install -r requirements.txt

# ==> Skipping migrations during build to avoid Session pooler limits
# Migrations should be run post-deploy or manually once the app is up.

echo "==> Collecting static files"
python backend/manage.py collectstatic --noinput

echo "==> Build complete"
