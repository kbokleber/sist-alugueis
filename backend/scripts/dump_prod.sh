#!/bin/sh
# Exporta o Postgres de producao para JSON (um arquivo por tabela).
# Uso (no servidor): sh scripts/dump_prod.sh
set -eu

OUT=/tmp/prod_dump
DB=$(docker ps --format '{{.Names}}' | grep '^db-' | head -n 1)

if [ -z "$DB" ]; then
    echo "ERRO: container do Postgres nao encontrado." >&2
    exit 1
fi

rm -rf "$OUT"
mkdir -p "$OUT"

TABLES="users properties financial_categories rental_revenues property_expenses audit_logs inventory_categories property_inventory_items stay_checklists stay_checklist_items"

for T in $TABLES; do
    echo "exportando $T..."
    docker exec "$DB" psql -U sist_alugueis -d sist_alugueis -At -c \
        "SELECT coalesce(json_agg(t), '[]'::json) FROM (SELECT * FROM $T) t;" \
        > "$OUT/$T.json"
    echo "  -> $(wc -c < "$OUT/$T.json") bytes"
done

docker exec "$DB" psql -U sist_alugueis -d sist_alugueis -At -c \
    "SELECT version_num FROM alembic_version;" > "$OUT/_alembic_version.txt" 2>/dev/null || true

ls -la "$OUT"
du -sh "$OUT"
