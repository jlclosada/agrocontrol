#!/usr/bin/env sh
set -e

echo "→ Applying database migrations..."
python manage.py migrate --noinput

echo "→ Collecting static files..."
python manage.py collectstatic --noinput >/dev/null 2>&1 || true

if [ "${SEED_DEMO:-true}" = "true" ]; then
  echo "→ Seeding demo data (idempotent)..."
  python manage.py seed_demo || true
fi

echo "→ Starting server: $*"
exec "$@"
