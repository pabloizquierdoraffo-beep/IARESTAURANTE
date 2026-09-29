"""Crea las tablas y el usuario de la aplicación.

Se ejecuta con el usuario dueño de la base de datos (no el de la aplicación):

    python -m app.preparar_bd "postgresql://dueño:...@servidor/basedatos" usuario_app contraseña_app

El usuario de la aplicación solo puede leer y escribir filas, y siempre con las reglas de
separación de clientes: no es dueño de las tablas, así que no puede saltárselas.
"""

import sys
from pathlib import Path

import psycopg
from psycopg import sql


def preparar(url_dueno: str, usuario_app: str, contrasena_app: str) -> None:
    esquema = (Path(__file__).parent / "esquema.sql").read_text(encoding="utf-8")
    with psycopg.connect(url_dueno, autocommit=True) as con:
        con.execute(esquema)
        existe = con.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (usuario_app,)).fetchone()
        accion = "ALTER" if existe else "CREATE"
        con.execute(sql.SQL(accion + " ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOBYPASSRLS").format(
            sql.Identifier(usuario_app), sql.Literal(contrasena_app)))
        base = con.execute("SELECT current_database() AS d").fetchone()[0]
        con.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(sql.Identifier(base), sql.Identifier(usuario_app)))
        con.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(usuario_app)))
        con.execute(sql.SQL("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {}").format(
            sql.Identifier(usuario_app)))
        # Los catálogos no los cambia la aplicación.
        con.execute(sql.SQL("REVOKE INSERT, UPDATE, DELETE ON planes, modulos FROM {}").format(sql.Identifier(usuario_app)))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    preparar(*sys.argv[1:])
    print("Base de datos preparada.")
