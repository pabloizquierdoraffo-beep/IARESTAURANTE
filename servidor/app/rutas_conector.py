"""Recepción de datos del conector, en el idioma común.

El paquete tiene exactamente la misma forma que envía el conector (conector/src/Conector.Nucleo).
Cualquier campo que no esté en el idioma común se rechaza entero: así, aunque un adaptador
fallara, un dato personal nunca entraría en la plataforma.
"""

from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from . import seguridad

router = APIRouter(prefix="/api/conector/v1")


class Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid", alias_generator=to_camel, populate_by_name=True)


class VentaHora(Modelo):
    local_id: str = Field(max_length=40)
    fecha: date
    hora: int = Field(ge=0, le=23)
    articulo_id: str = Field(max_length=40)
    articulo_nombre: str = Field(max_length=200)
    familia_id: str | None = Field(default=None, max_length=40)
    unidades: Decimal
    importe: Decimal


class TicketsHora(Modelo):
    local_id: str = Field(max_length=40)
    fecha: date
    hora: int = Field(ge=0, le=23)
    tickets: int = Field(ge=0)
    comensales: int = Field(ge=0)


class Familia(Modelo):
    id: str = Field(max_length=40)
    nombre: str = Field(max_length=200)
    familia_principal_id: str | None = Field(default=None, max_length=40)
    familia_principal_nombre: str | None = Field(default=None, max_length=200)


class Articulo(Modelo):
    id: str = Field(max_length=40)
    nombre: str = Field(max_length=200)
    familia_id: str | None = Field(default=None, max_length=40)
    se_vende: bool


class PrecioArticulo(Modelo):
    articulo_id: str = Field(max_length=40)
    tarifa_id: str = Field(max_length=40)
    precio: Decimal


class PaqueteDatos(Modelo):
    tpv: str = Field(max_length=40)
    desde: date
    hasta: date
    generado_en: datetime
    ventas: list[VentaHora]
    tickets: list[TicketsHora]
    familias: list[Familia]
    articulos: list[Articulo]
    precios: list[PrecioArticulo]


@router.post("/paquetes")
def recibir_paquete(paquete: PaqueteDatos, request: Request, authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Falta el token del conector.")
    if paquete.hasta <= paquete.desde or (paquete.hasta - paquete.desde).days > 400:
        raise HTTPException(status_code=422, detail="Rango de fechas no válido.")

    bd = request.app.state.bd
    with bd.conexion() as con:
        conector = con.execute("SELECT * FROM buscar_conector_por_token(%s)",
                               (seguridad.resumen_token(authorization.removeprefix("Bearer ").strip()),)).fetchone()
    if not conector:
        raise HTTPException(status_code=401, detail="Token de conector no válido.")

    # A partir de aquí todo va con el cliente del conector fijado: la base de datos no le deja
    # leer ni escribir datos de ningún otro cliente.
    with bd.conexion(conector["cliente_id"]) as con:
        # Solo los locales de este cliente que usan el mismo TPV que el conector.
        locales = {r["id_en_tpv"]: r["id"] for r in con.execute(
            "SELECT id, id_en_tpv FROM locales WHERE id_en_tpv IS NOT NULL AND tpv = %s", (conector["tpv"],)).fetchall()}
        recibidos = {v.local_id for v in paquete.ventas} | {t.local_id for t in paquete.tickets}
        desconocidos = sorted(recibidos - set(locales))
        if desconocidos:
            raise HTTPException(status_code=422, detail=f"Locales sin dar de alta en la plataforma: {', '.join(desconocidos)}.")

        cliente = conector["cliente_id"]
        fuera = [v for v in paquete.ventas if not paquete.desde <= v.fecha < paquete.hasta] + \
                [t for t in paquete.tickets if not paquete.desde <= t.fecha < paquete.hasta]
        if fuera:
            raise HTTPException(status_code=422, detail="Hay datos fuera del rango de fechas del paquete.")

        # Reenviar el mismo rango sustituye lo anterior (así un reenvío no duplica ventas).
        for tabla in ("ventas_hora", "tickets_hora"):
            con.execute(f"DELETE FROM {tabla} WHERE local_id = ANY(%s) AND fecha >= %s AND fecha < %s",
                        (list(locales.values()), paquete.desde, paquete.hasta))
        with con.cursor() as cur:
            cur.executemany(
                "INSERT INTO ventas_hora (cliente_id, local_id, fecha, hora, articulo_id, articulo_nombre, familia_id, unidades, importe) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [(cliente, locales[v.local_id], v.fecha, v.hora, v.articulo_id, v.articulo_nombre, v.familia_id, v.unidades, v.importe)
                 for v in paquete.ventas])
            cur.executemany(
                "INSERT INTO tickets_hora (cliente_id, local_id, fecha, hora, tickets, comensales) VALUES (%s, %s, %s, %s, %s, %s)",
                [(cliente, locales[t.local_id], t.fecha, t.hora, t.tickets, t.comensales) for t in paquete.tickets])
            cur.executemany(
                "INSERT INTO familias (cliente_id, id, nombre, principal_id, principal_nombre) VALUES (%s, %s, %s, %s, %s) "
                "ON CONFLICT (cliente_id, id) DO UPDATE SET nombre = excluded.nombre, principal_id = excluded.principal_id, "
                "principal_nombre = excluded.principal_nombre",
                [(cliente, f.id, f.nombre, f.familia_principal_id, f.familia_principal_nombre) for f in paquete.familias])
            cur.executemany(
                "INSERT INTO articulos (cliente_id, id, nombre, familia_id, se_vende) VALUES (%s, %s, %s, %s, %s) "
                "ON CONFLICT (cliente_id, id) DO UPDATE SET nombre = excluded.nombre, familia_id = excluded.familia_id, "
                "se_vende = excluded.se_vende",
                [(cliente, a.id, a.nombre, a.familia_id, a.se_vende) for a in paquete.articulos])
            cur.executemany(
                "INSERT INTO precios (cliente_id, articulo_id, tarifa_id, precio) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (cliente_id, articulo_id, tarifa_id) DO UPDATE SET precio = excluded.precio",
                [(cliente, p.articulo_id, p.tarifa_id, p.precio) for p in paquete.precios])
        con.execute("UPDATE conectores SET ultimo_envio = now() WHERE id = %s", (conector["conector_id"],))

    return {"ventas": len(paquete.ventas), "tickets": len(paquete.tickets), "familias": len(paquete.familias),
            "articulos": len(paquete.articulos), "precios": len(paquete.precios)}
