#!/usr/bin/env bash
# Prepara una copia de prueba de DSTNet para las pruebas automáticas del conector.
#
#   1. Arranca SQL Server en Docker (solo en el ordenador de pruebas; nunca en un bar).
#   2. Restaura la copia (.bak) que se le indique. La copia NUNCA se guarda en el repositorio.
#   3. Crea un usuario de SOLO LECTURA, que es el que usan las pruebas (igual que en un bar).
#
# Uso:
#   SA_PASSWORD='...' LECTOR_PASSWORD='...' ./preparar-bd-pruebas.sh /ruta/a/la/copia.bak
#
# Al terminar, muestra la variable CONECTOR_BD_PRUEBAS que hay que exportar para las pruebas.
set -euo pipefail

BAK="${1:?Indica la ruta de la copia .bak (puede venir comprimida en 7-Zip)}"
: "${SA_PASSWORD:?Falta SA_PASSWORD}"
: "${LECTOR_PASSWORD:?Falta LECTOR_PASSWORD}"
CONTENEDOR="${CONTENEDOR:-tpvsql}"
IMAGEN="mcr.microsoft.com/mssql/server:2022-latest"

TRABAJO="$(mktemp -d)"
trap 'rm -rf "$TRABAJO"' EXIT

# Las copias de DSTNet vienen comprimidas en 7-Zip aunque terminen en .bak.
if file "$BAK" | grep -q "7-zip"; then
  7z x -y -o"$TRABAJO" "$BAK" >/dev/null
  BAK_REAL="$(find "$TRABAJO" -name '*.bak' | head -n1)"
else
  cp "$BAK" "$TRABAJO/"
  BAK_REAL="$TRABAJO/$(basename "$BAK")"
fi
chmod 644 "$BAK_REAL"

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTENEDOR"; then
  docker rm -f "$CONTENEDOR" >/dev/null 2>&1 || true
  docker run -d --name "$CONTENEDOR" --network host \
    -e ACCEPT_EULA=Y -e MSSQL_PID=Developer -e "MSSQL_SA_PASSWORD=$SA_PASSWORD" \
    "$IMAGEN" >/dev/null
fi

sql() { docker exec "$CONTENEDOR" /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P "$SA_PASSWORD" -b "$@"; }

for _ in $(seq 1 60); do sql -Q "SELECT 1" >/dev/null 2>&1 && break; sleep 2; done

docker cp "$BAK_REAL" "$CONTENEDOR:/var/opt/mssql/data/pruebas.bak"
sql -Q "IF DB_ID('Central') IS NOT NULL BEGIN ALTER DATABASE Central SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE Central; END"
sql -Q "RESTORE DATABASE Central FROM DISK='/var/opt/mssql/data/pruebas.bak' WITH MOVE 'Central' TO '/var/opt/mssql/data/Central.mdf', MOVE 'Central_log' TO '/var/opt/mssql/data/Central_log.ldf'" >/dev/null
docker exec "$CONTENEDOR" rm -f /var/opt/mssql/data/pruebas.bak

# Usuario de solo lectura: puede leer, no puede escribir.
sql -Q "IF SUSER_ID('conector_lector') IS NULL CREATE LOGIN conector_lector WITH PASSWORD = '$LECTOR_PASSWORD', CHECK_POLICY = OFF; ELSE ALTER LOGIN conector_lector WITH PASSWORD = '$LECTOR_PASSWORD';"
sql -d Central -Q "IF USER_ID('conector_lector') IS NULL CREATE USER conector_lector FOR LOGIN conector_lector; ALTER ROLE db_datareader ADD MEMBER conector_lector; DENY INSERT, UPDATE, DELETE, EXECUTE, ALTER TO conector_lector;"

echo "Listo. Para las pruebas:"
echo "export CONECTOR_BD_PRUEBAS='Server=localhost;Database=Central;User Id=conector_lector;Password=<LECTOR_PASSWORD>;TrustServerCertificate=True'"
