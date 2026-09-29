"""Pantallas del dueño y del empleado."""

from datetime import date, timedelta

from app.comun import DIAS, entender_aviso
from app.datos_ejemplo import MOVIL_EMPLEADA_ESQUINA, cargar as cargar_ejemplo
from conftest import crear_cliente, csrf, entrar_bar


def test_avisar_en_dos_toques_pide_confirmacion_y_se_guarda(bd, cliente_web, mensajeria):
    crear_cliente(bd, "Bar A", "+34611111111")
    entrar_bar(cliente_web, mensajeria, "+34611111111")
    manana = date.today() + timedelta(days=1)
    r = cliente_web.get(f"/avisar?fecha={manana.isoformat()}")
    r = cliente_web.post("/avisar/preparar", data={"csrf": csrf(r), "fecha": manana.isoformat(), "motivo": "Partido"})
    assert "¿Lo he entendido bien?" in r.text
    with bd.conexion(plataforma=True) as con:
        assert con.execute("SELECT count(*) AS n FROM avisos").fetchone()["n"] == 0  # aún no se ha guardado
    r = cliente_web.post("/avisar/guardar", data={"csrf": csrf(r), "fecha": manana.isoformat(), "motivo": "Partido"})
    assert "Apuntado" in r.text
    with bd.conexion(plataforma=True) as con:
        aviso = con.execute("SELECT * FROM avisos").fetchone()
        assert aviso["fecha"] == manana and aviso["motivo"] == "Partido"


def test_avisar_con_sus_palabras(bd, cliente_web, mensajeria):
    crear_cliente(bd, "Bar A", "+34611111111")
    entrar_bar(cliente_web, mensajeria, "+34611111111")
    r = cliente_web.get("/avisar")
    r = cliente_web.post("/avisar/escrito", data={"csrf": csrf(r), "texto": "el viernes tengo una comunión de 60"})
    assert "Celebración (comunión)" in r.text and 'value="60"' in r.text and "inteligencia artificial" in r.text


def test_entender_aviso():
    hoy = date.today()
    dias = [hoy + timedelta(days=i) for i in range(14)]
    viernes = next(d for d in dias if d.weekday() == 4)
    r = entender_aviso("El VIERNES tengo una comunión de 60", dias)
    assert r == {"fecha": viernes, "motivo": "Celebración (comunión)", "personas": 60}
    sabado = next(d for d in dias if d.weekday() == 5)
    assert entender_aviso("el sabado cerramos", dias)["fecha"] == sabado
    assert entender_aviso("el sabado cerramos", dias)["motivo"] == "Cierre"
    assert entender_aviso("algo raro", dias) == {"fecha": None, "motivo": "Otra cosa", "personas": None}
    assert DIAS[viernes.weekday()] == "viernes"


def test_no_se_puede_avisar_para_un_dia_pasado(bd, cliente_web, mensajeria):
    crear_cliente(bd, "Bar A", "+34611111111")
    entrar_bar(cliente_web, mensajeria, "+34611111111")
    ayer = (date.today() - timedelta(days=1)).isoformat()
    r = cliente_web.get("/avisar")
    cliente_web.post("/avisar/guardar", data={"csrf": csrf(r), "fecha": ayer, "motivo": "Partido"})
    with bd.conexion(plataforma=True) as con:
        assert con.execute("SELECT count(*) AS n FROM avisos").fetchone()["n"] == 0


def test_el_empleado_no_ve_las_pantallas_del_dueno(urls, bd, cliente_web, mensajeria):
    cargar_ejemplo(urls["app"])
    r = entrar_bar(cliente_web, mensajeria, MOVIL_EMPLEADA_ESQUINA)
    assert r.headers["location"] == "/empleado"
    inicio = cliente_web.get("/empleado").text
    assert "Hola, Laura (ejemplo)" in inicio and "Empleados: fichaje, turnos y vacaciones" in inicio
    for ruta in ("/semana", "/avisar", "/ahorro", "/modulos"):
        assert cliente_web.get(ruta).status_code == 403


def test_pedir_informacion_de_un_modulo_queda_registrado(bd, cliente_web, mensajeria):
    crear_cliente(bd, "Bar A", "+34611111111")
    entrar_bar(cliente_web, mensajeria, "+34611111111")
    r = cliente_web.get("/modulos")
    assert "Escandallos, relevé y mermas" in r.text
    r = cliente_web.post("/modulos/informacion", data={"csrf": csrf(r), "modulo": "escandallos"})
    assert "Te llamaremos" in r.text
    with bd.conexion(plataforma=True) as con:
        assert con.execute("SELECT detalle FROM registro_acciones").fetchone()["detalle"] == "escandallos"


def test_cabeceras_de_seguridad(cliente_web):
    r = cliente_web.get("/")
    assert r.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in r.headers["Content-Security-Policy"]
