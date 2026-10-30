#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DB_HOST="${MSSQL_HOST:-localhost}"
DB_PORT="${MSSQL_PORT:-1433}"
DB_USER="${MSSQL_USER:-sa}"
DB_NAME="${MSSQL_DB:-FamilyConnect}"

: "${MSSQL_SA_PASSWORD:?Set MSSQL_SA_PASSWORD before running database/init.sh}"
if [[ ! "$DB_NAME" =~ ^[A-Za-z0-9_]+$ ]]; then
    echo "MSSQL_DB may contain only letters, numbers, and underscores." >&2
    exit 2
fi

export SQLCMDPASSWORD="$MSSQL_SA_PASSWORD"
SQLCMD=(sqlcmd -S "${DB_HOST},${DB_PORT}" -U "$DB_USER" -C -b -I -v "DB_NAME=$DB_NAME")

shopt -s nullglob

run_scripts() {
    local directory="$1"
    local -a files=("$directory"/*.sql)
    local file

    for file in "${files[@]}"; do
        echo "Running ${file##*/}"
        "${SQLCMD[@]}" -i "$file"
    done
}

run_scripts "$SCRIPT_DIR/schema"
run_scripts "$SCRIPT_DIR/seed"
