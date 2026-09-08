#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

: "${MEYLUX_DB_HOST:=localhost}"
: "${MEYLUX_DB_PORT:=5432}"
: "${MEYLUX_DB_NAME:?MEYLUX_DB_NAME must be set}"
: "${MEYLUX_DB_USER:=meylux_admin}"
: "${MEYLUX_DB_PASSWORD:?MEYLUX_DB_PASSWORD must be set}"

export PGPASSWORD="${MEYLUX_DB_PASSWORD}"

PSQL=(psql --host="${MEYLUX_DB_HOST}" --port="${MEYLUX_DB_PORT}" --username="${MEYLUX_DB_USER}" --dbname="${MEYLUX_DB_NAME}" --no-password --set=ON_ERROR_STOP=1)

"${PSQL[@]}" -f "${ROOT_DIR}/migrations/versions/0001_database_foundation.sql"

if [[ -n "${MEYLUX_APP_PASSWORD:-}" ]]; then
  "${PSQL[@]}" -v app_password="${MEYLUX_APP_PASSWORD}" -c "ALTER ROLE meylux_app LOGIN PASSWORD :'app_password';"
fi

if [[ -n "${MEYLUX_BACKUP_PASSWORD:-}" ]]; then
  "${PSQL[@]}" -v backup_password="${MEYLUX_BACKUP_PASSWORD}" -c "ALTER ROLE meylux_backup LOGIN PASSWORD :'backup_password';"
fi

"${PSQL[@]}" -c "ALTER DATABASE \"${MEYLUX_DB_NAME//\"/\"\"}\" SET timezone TO 'UTC';"

printf '%s\n' 'database migration: PASS'
