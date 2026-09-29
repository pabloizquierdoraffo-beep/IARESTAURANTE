"""Lo más importante: un cliente nunca puede ver ni tocar los datos de otro."""

import psycopg
import pytest

from conftest import crear_cliente, entrar_bar


def _venta(con, c, importe):
    con.execute("INSERT INTO ventas_hora (cliente_id, local_id, fecha, hora, articulo_id, articulo_nombre, unidades, importe) "
                "VALUES (%s, %s, '2026-06-27', 12, '138', 'CERVEZA', 1, %s)", (c["cliente_id"], c["local_id"], importe))


def test_la_base_de_datos_solo_ensena_las_filas_del_cliente_fijado(bd):
    a = crear_cliente(bd, "Bar A", "+34611111111")
    b = crear_cliente(bd, "Bar B", "+34622222222")
    with bd.conexion(plataforma=True) as con:
        _venta(con, a, 10)
        _venta(con, b, 99)

    with bd.conexion(a["cliente_id"]) as con:
        # Sin ningún filtro en la consulta: la base de datos ya filtra sola.
        assert [r["importe"] for r in con.execute("SELECT importe FROM ventas_hora").fetchall()] == [10]
        assert [r["nombre"] for r in con.execute("SELECT nombre FROM clientes").fetchall()] == ["Bar A"]
        assert [r["nombre"] for r in con.execute("SELECT nombre FROM locales").fetchall()] == ["Bar A"]
        assert con.execute("SELECT count(*) AS n FROM personas").fetchone()["n"] == 1
        # Intentar cambiar o borrar las ventas de B no afecta a ninguna fila.
        assert con.execute("UPDATE ventas_hora SET importe = 0 WHERE cliente_id = %s", (b["cliente_id"],)).rowcount == 0
        assert con.execute("DELETE FROM ventas_hora WHERE cliente_id = %s", (b["cliente_id"],)).rowcount == 0

    with bd.conexion(plataforma=True) as con:
        assert con.execute("SELECT importe FROM ventas_hora WHERE cliente_id = %s", (b["cliente_id"],)).fetchone()["importe"] == 99


def test_no_se_pueden_meter_datos_a_nombre_de_otro_cliente(bd):
    a = crear_cliente(bd, "Bar A", "+34611111111")
    b = crear_cliente(bd, "Bar B", "+34622222222")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with bd.conexion(a["cliente_id"]) as con:
            _venta(con, b, 5)


def test_sin_cliente_fijado_no_se_ve_nada(bd):
    crear_cliente(bd, "Bar A", "+34611111111")
    with bd.conexion() as con:
        assert con.execute("SELECT count(*) AS n FROM clientes").fetchone()["n"] == 0
        assert con.execute("SELECT count(*) AS n FROM locales").fetchone()["n"] == 0


def test_el_usuario_de_la_aplicacion_no_puede_saltarse_las_reglas(bd):
    with bd.conexion() as con:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            con.execute("ALTER TABLE ventas_hora DISABLE ROW LEVEL SECURITY")


def test_un_dueno_no_puede_ver_el_local_de_otro_aunque_cambie_la_direccion(bd, cliente_web, mensajeria):
    a = crear_cliente(bd, "Bar A", "+34611111111")
    b = crear_cliente(bd, "Bar B", "+34622222222")
    entrar_bar(cliente_web, mensajeria, "+34611111111")

    assert cliente_web.get("/semana").status_code == 200
    r = cliente_web.get(f"/semana?local={b['local_id']}")
    assert r.status_code == 404
    assert "Bar B" not in r.text
    assert cliente_web.get(f"/semana?local={a['local_id']}").status_code == 200
