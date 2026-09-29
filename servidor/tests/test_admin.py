"""Pantallas de la plataforma: alta de un bar, ficha, roles y resumen."""

from datetime import date

import pyotp

from app.comun import sumar_meses
from app.crear_usuario import crear as crear_usuario
from app.datos_ejemplo import MOVIL_DUENO_ESQUINA, cargar as cargar_ejemplo
from conftest import crear_cliente, csrf, entrar_bar


def entrar_como(urls, web, rol="admin"):
    email = f"{rol}@ejemplo.es"
    secreto = crear_usuario(urls["app"], email, rol, "una-contrasena-larga")
    r = web.get("/admin/entrar")
    r = web.post("/admin/entrar", data={"csrf": csrf(r), "email": email, "contrasena": "una-contrasena-larga"})
    web.post("/admin/verificar", data={"csrf": csrf(r), "codigo": pyotp.TOTP(secreto).now()})


def _alta(web, **cambios):
    datos = {"nombre": "Bar Nuevo", "municipio": "Huelva", "contacto": "Pepa", "movil": "633 33 33 33",
             "plan": "estandar", "locales": "2", "tpv": "DSTNet", "rgpd": "si"}
    datos.update(cambios)
    r = web.get("/admin/alta")
    return web.post("/admin/alta", data={"csrf": csrf(r), **datos}, follow_redirects=False)


def test_dar_de_alta_un_bar_empieza_la_prueba_de_2_meses_y_el_dueno_ya_puede_entrar(urls, bd, cliente_web, mensajeria, app):
    entrar_como(urls, cliente_web, "comercial")
    r = _alta(cliente_web)
    assert r.status_code == 303
    ficha = cliente_web.get(r.headers["location"])
    assert "Bar Nuevo" in ficha.text and "Cliente dado de alta" in ficha.text

    with bd.conexion(plataforma=True) as con:
        c = con.execute("SELECT * FROM clientes WHERE nombre = 'Bar Nuevo'").fetchone()
        assert c["estado"] == "prueba"
        assert c["prueba_hasta"] == sumar_meses(date.today(), 2)
        assert con.execute("SELECT count(*) AS n FROM locales WHERE cliente_id = %s", (c["id"],)).fetchone()["n"] == 2

    bar = type(cliente_web)(app)
    assert entrar_bar(bar, mensajeria, "+34633333333").headers["location"] == "/semana"


def test_sin_contrato_rgpd_no_hay_alta(urls, cliente_web):
    entrar_como(urls, cliente_web)
    r = _alta(cliente_web, rgpd="")
    assert "contrato de protección de datos" in r.text


def test_un_movil_no_puede_estar_en_dos_clientes(urls, bd, cliente_web):
    crear_cliente(bd, "Bar A", "+34633333333")
    entrar_como(urls, cliente_web)
    assert "ya está dado de alta" in _alta(cliente_web).text


def test_comercial_no_puede_cambiar_plan_ni_modulos_ni_crear_conectores(urls, bd, cliente_web):
    a = crear_cliente(bd, "Bar A", "+34611111111")
    entrar_como(urls, cliente_web, "comercial")
    token = csrf(cliente_web.get(f"/admin/clientes/{a['cliente_id']}"))
    for ruta, datos in (("plan", {"plan": "grupo"}), ("modulos", {"modulo_turnos": "si"}), ("conector", {"tpv": "DSTNet"})):
        assert cliente_web.post(f"/admin/clientes/{a['cliente_id']}/{ruta}", data={"csrf": token, **datos}).status_code == 403
    with bd.conexion(plataforma=True) as con:
        assert con.execute("SELECT plan FROM clientes").fetchone()["plan"] == "basico"


def test_admin_cambia_plan_y_modulos_y_queda_registrado(urls, bd, cliente_web):
    a = crear_cliente(bd, "Bar A", "+34611111111")
    entrar_como(urls, cliente_web)
    url = f"/admin/clientes/{a['cliente_id']}"
    token = csrf(cliente_web.get(url))
    cliente_web.post(url + "/plan", data={"csrf": token, "plan": "grupo"})
    cliente_web.post(url + "/modulos", data={"csrf": token, "modulo_turnos": "si", "modulo_escandallos": "si", "modulo_inventado": "si"})
    with bd.conexion(plataforma=True) as con:
        assert con.execute("SELECT plan FROM clientes").fetchone()["plan"] == "grupo"
        assert sorted(r["modulo"] for r in con.execute("SELECT modulo FROM modulos_contratados").fetchall()) == ["escandallos", "turnos"]
        assert con.execute("SELECT count(*) AS n FROM registro_acciones").fetchone()["n"] == 2
    cliente_web.post(url + "/modulos", data={"csrf": token, "modulo_turnos": "si"})
    with bd.conexion(plataforma=True) as con:
        assert [r["modulo"] for r in con.execute("SELECT modulo FROM modulos_contratados").fetchall()] == ["turnos"]


def test_el_token_del_conector_solo_se_ensena_una_vez_y_no_se_guarda(urls, bd, cliente_web):
    a = crear_cliente(bd, "Bar A", "+34611111111")
    entrar_como(urls, cliente_web)
    url = f"/admin/clientes/{a['cliente_id']}"
    r = cliente_web.post(url + "/conector", data={"csrf": csrf(cliente_web.get(url)), "tpv": "DSTNet"})
    token = r.text.split('<p class="token">')[1].split("</p>")[0]
    assert len(token) > 30
    assert token not in cliente_web.get(url).text
    with bd.conexion(plataforma=True) as con:
        assert con.execute("SELECT hash_token FROM conectores").fetchone()["hash_token"] != token


def test_mensaje_de_prueba(urls, bd, cliente_web, mensajeria):
    a = crear_cliente(bd, "Bar A", "+34611111111")
    entrar_como(urls, cliente_web, "comercial")
    url = f"/admin/clientes/{a['cliente_id']}"
    r = cliente_web.post(url + "/mensaje-prueba", data={"csrf": csrf(cliente_web.get(url))})
    assert "Mensaje de prueba enviado" in r.text
    assert mensajeria.enviados[0][0] == "+34611111111"


def test_el_resumen_senala_a_quien_hay_que_atender(urls, bd, cliente_web):
    cargar_ejemplo(urls["app"])
    entrar_como(urls, cliente_web)
    texto = cliente_web.get("/admin").text
    assert "Taberna Los Arcos (ejemplo): el conector lleva más de 24 horas sin enviar datos." in texto
    assert "Cervecería El Grifo (ejemplo): no ha abierto los últimos 3 mensajes." in texto
    assert "Café Plaza (ejemplo): la prueba gratis acaba en 4 días." in texto
    clientes = cliente_web.get("/admin/clientes").text
    for estado in ("Sin conexión", "Riesgo de baja", "En prueba", "Activo"):
        assert estado in clientes


def test_los_datos_de_ejemplo_van_marcados(urls, bd, cliente_web, mensajeria):
    cargar_ejemplo(urls["app"])
    with bd.conexion(plataforma=True) as con:
        assert con.execute("SELECT bool_and(es_ejemplo) AS t FROM clientes").fetchone()["t"]
        assert con.execute("SELECT bool_and(es_ejemplo) AS t FROM personas").fetchone()["t"]
    entrar_bar(cliente_web, mensajeria, MOVIL_DUENO_ESQUINA)
    semana = cliente_web.get("/semana").text
    assert "Previsión de ejemplo" in semana and "entre 180 y 220 clientes" in semana
    assert "La decisión final es tuya" in semana
