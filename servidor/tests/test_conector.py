"""Recepción de datos del conector."""

from app import seguridad
from conftest import crear_cliente


def _conector(bd, cliente_id) -> str:
    token = seguridad.nuevo_token_conector()
    with bd.conexion(plataforma=True) as con:
        con.execute("INSERT INTO conectores (cliente_id, tpv, hash_token) VALUES (%s, 'DSTNet', %s)",
                    (cliente_id, seguridad.resumen_token(token)))
    return token


def _paquete(local="1-1", **extra_venta):
    venta = {"localId": local, "fecha": "2026-06-27", "hora": 12, "articuloId": "138", "articuloNombre": "CERVEZA",
             "familiaId": "10006", "unidades": 12, "importe": 18.0, **extra_venta}
    return {
        "tpv": "DSTNet", "desde": "2026-06-27", "hasta": "2026-06-28", "generadoEn": "2026-06-28T02:00:00+00:00",
        "ventas": [venta],
        "tickets": [{"localId": local, "fecha": "2026-06-27", "hora": 12, "tickets": 16, "comensales": 16}],
        "familias": [{"id": "10006", "nombre": "CERVEZAS NACIONALES", "familiaPrincipalId": "1", "familiaPrincipalNombre": "BEBIDAS"}],
        "articulos": [{"id": "138", "nombre": "CERVEZA", "familiaId": "10006", "seVende": True}],
        "precios": [{"articuloId": "138", "tarifaId": "0", "precio": 1.5}],
    }


def _enviar(web, token, paquete):
    return web.post("/api/conector/v1/paquetes", json=paquete, headers={"Authorization": f"Bearer {token}"})


def test_guarda_el_paquete_y_marca_el_ultimo_envio(bd, cliente_web):
    a = crear_cliente(bd, "Bar A", "+34611111111")
    token = _conector(bd, a["cliente_id"])
    r = _enviar(cliente_web, token, _paquete())
    assert r.status_code == 200, r.text
    assert r.json() == {"ventas": 1, "tickets": 1, "familias": 1, "articulos": 1, "precios": 1}
    with bd.conexion(a["cliente_id"]) as con:
        assert con.execute("SELECT importe FROM ventas_hora").fetchone()["importe"] == 18
        assert con.execute("SELECT ultimo_envio FROM conectores").fetchone()["ultimo_envio"] is not None


def test_reenviar_el_mismo_dia_no_duplica(bd, cliente_web):
    a = crear_cliente(bd, "Bar A", "+34611111111")
    token = _conector(bd, a["cliente_id"])
    _enviar(cliente_web, token, _paquete())
    _enviar(cliente_web, token, _paquete(importe=20.0))
    with bd.conexion(a["cliente_id"]) as con:
        assert [r["importe"] for r in con.execute("SELECT importe FROM ventas_hora").fetchall()] == [20]


def test_rechaza_cualquier_campo_que_no_sea_del_idioma_comun(bd, cliente_web):
    a = crear_cliente(bd, "Bar A", "+34611111111")
    token = _conector(bd, a["cliente_id"])
    for extra in ({"employee": 4}, {"nif": "12345678Z"}, {"observation": "texto libre"}):
        assert _enviar(cliente_web, token, _paquete(**extra)).status_code == 422
    paquete = _paquete()
    paquete["telefono"] = "600000000"
    assert _enviar(cliente_web, token, paquete).status_code == 422
    with bd.conexion(plataforma=True) as con:
        assert con.execute("SELECT count(*) AS n FROM ventas_hora").fetchone()["n"] == 0


def test_sin_token_o_con_token_falso_no_entra_nada(bd, cliente_web):
    crear_cliente(bd, "Bar A", "+34611111111")
    assert cliente_web.post("/api/conector/v1/paquetes", json=_paquete()).status_code == 401
    assert _enviar(cliente_web, "inventado", _paquete()).status_code == 401


def test_el_conector_de_un_cliente_no_puede_escribir_en_otro(bd, cliente_web):
    a = crear_cliente(bd, "Bar A", "+34611111111", id_en_tpv="1-1")
    b = crear_cliente(bd, "Bar B", "+34622222222", id_en_tpv="9-9")
    token_a = _conector(bd, a["cliente_id"])
    # El conector de A intenta mandar ventas del local de B: B no existe para A.
    r = _enviar(cliente_web, token_a, _paquete(local="9-9"))
    assert r.status_code == 422 and "9-9" in r.json()["detail"]
    with bd.conexion(plataforma=True) as con:
        assert con.execute("SELECT count(*) AS n FROM ventas_hora WHERE cliente_id = %s", (b["cliente_id"],)).fetchone()["n"] == 0


def test_rechaza_datos_fuera_del_rango_de_fechas(bd, cliente_web):
    a = crear_cliente(bd, "Bar A", "+34611111111")
    token = _conector(bd, a["cliente_id"])
    assert _enviar(cliente_web, token, _paquete(fecha="2026-07-15")).status_code == 422
