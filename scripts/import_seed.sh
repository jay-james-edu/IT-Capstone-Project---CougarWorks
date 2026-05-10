#!/usr/bin/env bash
set -euo pipefail

# Imports the fake/demo seed JSON into a running local MongoDB container.
# Usage:
#   docker compose -f compose.yml up -d mongo
#   ./scripts/import_seed.sh

DB_NAME="${MONGO_DB_NAME:-CougarWorks}"
MONGO_USER="${MONGO_USER:-cougarworks_app}"
MONGO_PASS="${MONGO_PASS:-change-this-mongo-password}"
MONGO_HOST="${MONGO_HOST:-localhost}"
MONGO_PORT="${MONGO_PORT:-27017}"
AUTH_DB="${MONGO_AUTH_DB:-admin}"
SEED_DIR="${SEED_DIR:-database/seeds}"

for file in "$SEED_DIR"/*.json; do
  collection="$(basename "$file" .json)"
  echo "Importing $file into $DB_NAME.$collection"
  mongoimport \
    --host "$MONGO_HOST" \
    --port "$MONGO_PORT" \
    --username "$MONGO_USER" \
    --password "$MONGO_PASS" \
    --authenticationDatabase "$AUTH_DB" \
    --db "$DB_NAME" \
    --collection "$collection" \
    --jsonArray \
    --drop \
    --file "$file"
done

echo "Seed import complete."
