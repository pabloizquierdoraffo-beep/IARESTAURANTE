"""Acceso del bar (móvil + código) y de la plataforma (correo + contraseña + app de verificación)."""

import pyotp

from app.crear_usuario import crear as crear_usuario
from conftest import crear_cliente, csrf, entrar_bar


def test_el_dueno_entra_con_su_movil_y_el_codigo(bd, cliente_web, mensajeria):
    crear_cliente(bd, "Bar A", "+34611111111")
    r = entrar_bar(cliente_web, mensajeria, "611 11 11 11")
    assert r.status_code == 303 and r.headers["location"] == "/semana"
    assert "Aún no hay previsión" in cliente_web.get("/semana").text


def test_sin_entrar_no_se_ve_nada_del_bar(cliente_web):
    for ruta in ("/semana", "/avisar", "/ahorro", "/modulos", "/empleado"):
        r = cliente_web.get(ruta, follow_redirects=False)
        assert r.status_code == 303 and r.headers["location"] == "/entrar"


def test_un_movil_desconocido_recibe_la_misma_respuesta_pero_ningun_codigo(bd, cliente_web, mensajeria):
    r = cliente_web.get("/entrar")
    r = cliente_web.post("/entrar", data={"csrf": csrf(r), "movil": "699999999"}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/entrar/codigo"
    assert mensajeria.ultimo_codigo == {}


def test_despues_de_5_intentos_fallidos_el_codigo_deja_de_valer(bd, cliente_web, mensajeria):
    crear_cliente(bd, "Bar A", "+34611111111")
    r = cliente_web.get("/entrar")
    cliente_web.post("/entrar", data={"csrf": csrf(r), "movil": "611111111"})
    bueno = mensajeria.ultimo_codigo["+34611111111"]
    malo = "000000" if bueno != "000000" else "111111"
    for _ in range(5):
        r = cliente_web.get("/entrar/codigo")
        assert "no es correcto" in cliente_web.post("/entrar/codigo", data={"csrf": csrf(r), "codigo": malo}).text
    r = cliente_web.get("/entrar/codigo")
    r = cliente_web.post("/entrar/codigo", data={"csrf": csrf(r), "codigo": bueno})
    assert "Demasiados intentos" in r.text


def test_un_codigo_caducado_no_vale(bd, cliente_web, mensajeria):
    crear_cliente(bd, "Bar A", "+34611111111")
    r = cliente_web.get("/entrar")
    cliente_web.post("/entrar", data={"csrf": csrf(r), "movil": "611111111"})
    with bd.conexion() as con:
        con.execute("UPDATE codigos_acceso SET caduca_en = now() - interval '1 minute'")
    r = cliente_web.get("/entrar/codigo")
    r = cliente_web.post("/entrar/codigo", data={"csrf": csrf(r), "codigo": mensajeria.ultimo_codigo["+34611111111"]})
    assert "no es correcto o ha caducado" in r.text


def test_como_mucho_3_codigos_cada_15_minutos(bd, cliente_web, mensajeria):
    crear_cliente(bd, "Bar A", "+34611111111")
    for _ in range(5):
        r = cliente_web.get("/entrar")
        cliente_web.post("/entrar", data={"csrf": csrf(r), "movil": "611111111"})
    with bd.conexion() as con:
        assert con.execute("SELECT count(*) AS n FROM codigos_acceso").fetchone()["n"] == 3


def test_un_formulario_sin_la_marca_de_seguridad_se_rechaza(bd, cliente_web):
    r = cliente_web.post("/entrar", data={"movil": "611111111"})
    assert r.status_code == 403


def _entrar_admin(web, email, contrasena, codigo):
    r = web.get("/admin/entrar")
    r = web.post("/admin/entrar", data={"csrf": csrf(r), "email": email, "contrasena": contrasena})
    return web.post("/admin/verificar", data={"csrf": csrf(r), "codigo": codigo}, follow_redirects=False)


def test_la_plataforma_pide_contrasena_y_codigo_de_la_app(urls, cliente_web):
    secreto = crear_usuario(urls["app"], "admin@ejemplo.es", "admin", "una-contrasena-larga")
    # Solo con la contraseña no se entra.
    r = cliente_web.get("/admin/entrar")
    cliente_web.post("/admin/entrar", data={"csrf": csrf(r), "email": "admin@ejemplo.es", "contrasena": "una-contrasena-larga"})
    assert cliente_web.get("/admin", follow_redirects=False).headers["location"] == "/admin/entrar"
    # Con un código equivocado, tampoco.
    r = cliente_web.get("/admin/verificar")
    assert "no es correcto" in cliente_web.post("/admin/verificar", data={"csrf": csrf(r), "codigo": "000000"}).text
    # Con la contraseña y el código bueno, sí.
    r = _entrar_admin(cliente_web, "admin@ejemplo.es", "una-contrasena-larga", pyotp.TOTP(secreto).now())
    assert r.headers["location"] == "/admin"
    assert cliente_web.get("/admin").status_code == 200


def test_contrasena_equivocada(urls, cliente_web):
    crear_usuario(urls["app"], "admin@ejemplo.es", "admin", "una-contrasena-larga")
    r = cliente_web.get("/admin/entrar")
    r = cliente_web.post("/admin/entrar", data={"csrf": csrf(r), "email": "admin@ejemplo.es", "contrasena": "otra"})
    assert "incorrectos" in r.text


def test_un_dueno_de_bar_no_entra_en_la_administracion(bd, cliente_web, mensajeria):
    crear_cliente(bd, "Bar A", "+34611111111")
    entrar_bar(cliente_web, mensajeria, "+34611111111")
    assert cliente_web.get("/admin", follow_redirects=False).headers["location"] == "/admin/entrar"
