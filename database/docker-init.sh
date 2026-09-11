#!/bin/bash
# Applies all shared migrations then all seed files, in filename order.
# Mounted into /docker-entrypoint-initdb.d so it runs once on first container init.
set -e

for f in /database/migrations/*.sql; do
  echo "Applying migration: $f"
  psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$f"
done

for f in /database/seed/*.sql; do
  echo "Applying seed: $f"
  psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$f"
done
