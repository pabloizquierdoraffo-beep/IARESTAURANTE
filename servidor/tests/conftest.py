"""Prepara una base de datos PostgreSQL nueva para las pruebas.

Necesita PRUEBAS_PG_ADMIN_URL (usuario que pueda crear bases de datos), por ejemplo:
    postgresql://postgres:clave@localhost/postgres
Si no está, las pruebas se saltan.
"""

import os
import re
import uuid

import psycopg
import pytest
from fastapi.testclient import TestClient

from app import config as configuracion
from app import seguridad
from app import preparar_bd
from app.db import BaseDatos
from app.main import crear_app
from app.mensajeria import MensajeriaDesarrollo

ADMIN_URL = os.environ.get("PRUEBAS_PG_ADMIN_URL")
USUARIO_APP = "app_web_pruebas"
CLAVE_APP = "clave_app_pruebas_" + uuid.uuid4().hex[:8]

TABLAS_CLIENTE = ["clientes", "usuarios_plataforma", "codigos_acceso"]


def _url(base: str, nombre_bd: str, usuario: str | None = None, clave: str | None = None) -> str:
    info = psycopg.conninfo.conninfo_to_dict(base)
    info["dbname"] = nombre_bd
    if usuario:
        info["user"], info["password"] = usuario, clave
    return psycopg.conninfo.make_conninfo(**info)


@pytest.fixture(scope="session")
def urls():
    if not ADMIN_URL:
        pytest.skip("Falta PRUEBAS_PG_ADMIN_URL: no hay PostgreSQL para las pruebas.")
    nombre = "pruebas_" + uuid.uuid4().hex[:10]
    with psycopg.connect(ADMIN_URL, autocommit=True) as con:
        con.execute(f'CREATE DATABASE "{nombre}"')
    dueno = _url(ADMIN_URL, nombre)
    preparar_bd.preparar(dueno, USUARIO_APP, CLAVE_APP)
    yield {"dueno": dueno, "app": _url(ADMIN_URL, nombre, USUARIO_APP, CLAVE_APP)}
    with psycopg.connect(ADMIN_URL, autocommit=True) as con:
        con.execute(f'DROP DATABASE "{nombre}" WITH (FORCE)')


@pytest.fixture(autouse=True)
def limpiar(request):
    yield
    if "urls" in request.fixturenames:
        urls = request.getfixturevalue("urls")
        with psycopg.connect(urls["dueno"], autocommit=True) as con:
            con.execute("TRUNCATE " + ", ".join(TABLAS_CLIENTE) + " CASCADE")


@pytest.fixture
def bd(urls):
    return BaseDatos(urls["app"])


@pytest.fixture
def mensajeria():
    return MensajeriaDesarrollo()


@pytest.fixture
def app(urls, mensajeria):
    config = configuracion.Config(
        database_url=urls["app"], clave_secreta="x" * 40, modo_desarrollo=True, cookies_seguras=False,
        soporte_nombre="Soporte", soporte_telefono="600 000 000")
    return crear_app(config, mensajeria)


@pytest.fixture
def cliente_web(app):
    return TestClient(app)


def csrf(respuesta) -> str:
    return re.search(r'name="csrf" value="([^"]+)"', respuesta.text).group(1)


def crear_cliente(bd: BaseDatos, nombre: str, movil_dueno: str, id_en_tpv: str = "1-1") -> dict:
    """Crea un cliente con un local y un dueño. Devuelve sus ids."""
    with bd.conexion(plataforma=True) as con:
        cid = con.execute(
            "INSERT INTO clientes (nombre, municipio, contacto_nombre, contacto_movil, plan, estado, rgpd_firmado_en) "
            "VALUES (%s, 'Sevilla', 'Contacto', %s, 'basico', 'activo', now()) RETURNING id", (nombre, movil_dueno)).fetchone()["id"]
        lid = con.execute("INSERT INTO locales (cliente_id, nombre, municipio, tpv, id_en_tpv) VALUES (%s, %s, 'Sevilla', 'DSTNet', %s) "
                          "RETURNING id", (cid, nombre, id_en_tpv)).fetchone()["id"]
        pid = con.execute("INSERT INTO personas (cliente_id, nombre, movil, rol) VALUES (%s, 'Dueño', %s, 'dueno') RETURNING id",
                          (cid, movil_dueno)).fetchone()["id"]
    return {"cliente_id": cid, "local_id": lid, "persona_id": pid}


def entrar_bar(web: TestClient, mensajeria: MensajeriaDesarrollo, movil: str):
    r = web.get("/entrar")
    web.post("/entrar", data={"csrf": csrf(r), "movil": movil})
    r = web.get("/entrar/codigo")
    codigo = mensajeria.ultimo_codigo[seguridad.normalizar_movil(movil)]
    return web.post("/entrar/codigo", data={"csrf": csrf(r), "codigo": codigo}, follow_redirects=False)
