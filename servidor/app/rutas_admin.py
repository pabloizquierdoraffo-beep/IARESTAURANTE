"""Pantallas de la plataforma (nosotros). Correo + contraseña + código de la app de verificación.

Roles: «admin» puede todo; «comercial» (y soporte) puede dar de alta, ver y enviar mensajes de
prueba, pero no cambiar planes, módulos ni conectores.
"""

import time
from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from . import seguridad
from .comun import comprobar_formulario, pagina, sumar_meses

router = APIRouter(prefix="/admin")

DURACION_SESION = 8 * 3600
EQUILIBRIO_LOCALES = 184
DURACION_PRUEBA_MESES = 2


class NecesitaEntrarAdmin(Exception):
    pass


def _bd(request: Request):
    return request.app.state.bd


def admin_actual(request: Request, solo_admin: bool = False) -> dict:
    admin = request.session.get("admin")
    if not admin or time.time() - admin["desde"] > DURACION_SESION:
        request.session.pop("admin", None)
        raise NecesitaEntrarAdmin()
    if solo_admin and admin["rol"] != "admin":
        raise HTTPException(status_code=403, detail="Solo un administrador puede hacer esto.")
    return admin


def _registrar(con, cliente_id, admin: dict, accion: str, detalle: str | None = None):
    con.execute("INSERT INTO registro_acciones (cliente_id, quien, accion, detalle) VALUES (%s, %s, %s, %s)",
                (cliente_id, admin["email"], accion, detalle))


# ---------- Acceso ----------

@router.get("/entrar")
def entrar(request: Request):
    return pagina(request, "admin_entrar.html", error=None)


@router.post("/entrar")
async def entrar_comprobar(request: Request):
    datos = await comprobar_formulario(request)
    email = str(datos.get("email", "")).strip().lower()
    with _bd(request).conexion(plataforma=True) as con:
        usuario = con.execute("SELECT * FROM usuarios_plataforma WHERE email = %s AND activo", (email,)).fetchone()
    if not usuario or not seguridad.comprobar_contrasena(usuario["hash_contrasena"], str(datos.get("contrasena", ""))):
        return pagina(request, "admin_entrar.html", error="Correo o contraseña incorrectos.")
    request.session.clear()
    request.session["admin_pendiente"] = {"id": str(usuario["id"]), "desde": time.time()}
    return RedirectResponse("/admin/verificar", status_code=303)


@router.get("/verificar")
def verificar(request: Request):
    if not request.session.get("admin_pendiente"):
        return RedirectResponse("/admin/entrar", status_code=303)
    return pagina(request, "admin_verificar.html", error=None)


@router.post("/verificar")
async def verificar_comprobar(request: Request):
    datos = await comprobar_formulario(request)
    pendiente = request.session.get("admin_pendiente")
    if not pendiente or time.time() - pendiente["desde"] > 300:
        request.session.pop("admin_pendiente", None)
        return RedirectResponse("/admin/entrar", status_code=303)
    with _bd(request).conexion(plataforma=True) as con:
        usuario = con.execute("SELECT * FROM usuarios_plataforma WHERE id = %s AND activo", (pendiente["id"],)).fetchone()
    if not usuario or not seguridad.comprobar_totp(usuario["totp_secreto"], str(datos.get("codigo", ""))):
        return pagina(request, "admin_verificar.html", error="El código no es correcto. Mira la app de verificación.")
    request.session.clear()
    request.session["admin"] = {"id": str(usuario["id"]), "email": usuario["email"], "rol": usuario["rol"], "desde": time.time()}
    return RedirectResponse("/admin", status_code=303)


@router.get("/salir")
def salir(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/entrar", status_code=303)


# ---------- Datos de los clientes ----------

CONSULTA_CLIENTES = """
SELECT c.*, p.nombre AS plan_nombre, p.precio_eur,
       (SELECT count(*) FROM locales l WHERE l.cliente_id = c.id) AS n_locales,
       (SELECT count(*) FROM conectores k WHERE k.cliente_id = c.id) AS n_conectores,
       (SELECT max(k.ultimo_envio) FROM conectores k WHERE k.cliente_id = c.id) AS ultimo_envio,
       (SELECT min(k.creado_en) FROM conectores k WHERE k.cliente_id = c.id) AS conector_desde,
       (SELECT count(*) FROM (SELECT leido_en FROM mensajes m WHERE m.cliente_id = c.id
                              ORDER BY enviado_en DESC LIMIT 3) u) AS ultimos_mensajes,
       (SELECT count(*) FROM (SELECT leido_en FROM mensajes m WHERE m.cliente_id = c.id
                              ORDER BY enviado_en DESC LIMIT 3) u WHERE u.leido_en IS NOT NULL) AS ultimos_leidos,
       (SELECT coalesce(array_agg(m.nombre ORDER BY m.orden), '{}') FROM modulos_contratados mc
          JOIN modulos m ON m.codigo = mc.modulo WHERE mc.cliente_id = c.id) AS modulos
FROM clientes c JOIN planes p ON p.codigo = c.plan
"""


def _estado(c: dict, ahora) -> tuple[str, str]:
    """Estado visible de un cliente: (texto, tipo de etiqueta)."""
    if c["estado"] == "baja":
        return "Baja", "normal"
    hace_24h = ahora - timedelta(hours=24)
    if c["n_conectores"] and ((c["ultimo_envio"] or c["conector_desde"]) < hace_24h):
        return "Sin conexión", "mal"
    if c["ultimos_mensajes"] >= 3 and c["ultimos_leidos"] == 0:
        return "Riesgo de baja", "aviso"
    if c["estado"] == "prueba":
        return "En prueba", "normal"
    return "Activo", "ok"


def _clientes(con, where: str = "", params: tuple = ()) -> list[dict]:
    ahora = con.execute("SELECT now() AS t").fetchone()["t"]
    filas = con.execute(CONSULTA_CLIENTES + where + " ORDER BY c.nombre", params).fetchall()
    for c in filas:
        c["estado_texto"], c["estado_tipo"] = _estado(c, ahora)
        c["cuota"] = 0 if c["estado"] == "prueba" else c["precio_eur"] * max(c["n_locales"], 1)
    return filas


@router.get("")
def resumen(request: Request):
    admin = admin_actual(request)
    hoy = date.today()
    with _bd(request).conexion(plataforma=True) as con:
        clientes = _clientes(con)
        locales_conectados = con.execute(
            "SELECT count(DISTINCT l.id) AS n FROM locales l JOIN conectores k ON k.cliente_id = l.cliente_id "
            "WHERE k.ultimo_envio IS NOT NULL").fetchone()["n"]
    tareas = []
    for c in clientes:
        if c["estado_texto"] == "Sin conexión":
            tareas.append(("mal", "Sin datos", f"{c['nombre']}: el conector lleva más de 24 horas sin enviar datos.", c))
    for c in clientes:
        if c["estado_texto"] == "Riesgo de baja":
            tareas.append(("aviso", "No lee", f"{c['nombre']}: no ha abierto los últimos 3 mensajes.", c))
    for c in clientes:
        if c["estado"] == "prueba" and c["prueba_hasta"] and c["prueba_hasta"] - hoy <= timedelta(days=7):
            dias = (c["prueba_hasta"] - hoy).days
            tareas.append(("normal", "Prueba", f"{c['nombre']}: la prueba gratis acaba en {dias} días.", c))
    return pagina(request, "admin_resumen.html", admin=admin, seccion="resumen",
                  ingresos=sum(c["cuota"] for c in clientes if c["estado"] == "activo"),
                  locales_conectados=locales_conectados, equilibrio=EQUILIBRIO_LOCALES,
                  en_prueba=sum(1 for c in clientes if c["estado"] == "prueba"),
                  atencion=len({t[3]["id"] for t in tareas}), tareas=tareas)


@router.get("/clientes")
def clientes(request: Request):
    admin = admin_actual(request)
    with _bd(request).conexion(plataforma=True) as con:
        lista = _clientes(con)
    return pagina(request, "admin_clientes.html", admin=admin, seccion="clientes", clientes=lista)


@router.get("/clientes/{cliente_id}")
def ficha(request: Request, cliente_id: UUID, hecho: str | None = None):
    admin = admin_actual(request)
    with _bd(request).conexion(plataforma=True) as con:
        encontrados = _clientes(con, " WHERE c.id = %s", (cliente_id,))
        if not encontrados:
            raise HTTPException(status_code=404)
        locales = con.execute("SELECT * FROM locales WHERE cliente_id = %s ORDER BY nombre", (cliente_id,)).fetchall()
        personas = con.execute("SELECT nombre, movil, rol FROM personas WHERE cliente_id = %s ORDER BY rol, nombre", (cliente_id,)).fetchall()
        conectores = con.execute("SELECT * FROM conectores WHERE cliente_id = %s ORDER BY creado_en", (cliente_id,)).fetchall()
        planes = con.execute("SELECT * FROM planes ORDER BY precio_eur").fetchall()
        modulos = con.execute(
            "SELECT m.*, (mc.modulo IS NOT NULL) AS contratado FROM modulos m LEFT JOIN modulos_contratados mc "
            "ON mc.modulo = m.codigo AND mc.cliente_id = %s WHERE NOT m.incluido ORDER BY m.orden", (cliente_id,)).fetchall()
        acciones = con.execute("SELECT * FROM registro_acciones WHERE cliente_id = %s ORDER BY creado_en DESC LIMIT 10",
                               (cliente_id,)).fetchall()
    return pagina(request, "admin_ficha.html", admin=admin, seccion="clientes", c=encontrados[0], locales=locales,
                  personas=personas, conectores=conectores, planes=planes, modulos=modulos, acciones=acciones,
                  hecho=hecho)


def _dueno(con, cliente_id):
    return con.execute("SELECT movil FROM personas WHERE cliente_id = %s AND rol = 'dueno' ORDER BY nombre LIMIT 1",
                       (cliente_id,)).fetchone()


@router.post("/clientes/{cliente_id}/mensaje-prueba")
async def mensaje_prueba(request: Request, cliente_id: UUID):
    admin = admin_actual(request)
    await comprobar_formulario(request)
    with _bd(request).conexion(plataforma=True) as con:
        dueno = _dueno(con, cliente_id)
        if not dueno:
            raise HTTPException(status_code=404)
        con.execute("INSERT INTO mensajes (cliente_id, tipo) VALUES (%s, 'prueba')", (cliente_id,))
        _registrar(con, cliente_id, admin, "envía mensaje de prueba")
    request.app.state.mensajeria.enviar_texto(dueno["movil"], "Mensaje de prueba de la plataforma. Si lo ves, todo funciona.")
    return RedirectResponse(f"/admin/clientes/{cliente_id}?hecho=mensaje", status_code=303)


@router.post("/clientes/{cliente_id}/avisar-tecnico")
async def avisar_tecnico(request: Request, cliente_id: UUID):
    admin = admin_actual(request)
    await comprobar_formulario(request)
    with _bd(request).conexion(plataforma=True) as con:
        if not con.execute("SELECT 1 FROM clientes WHERE id = %s", (cliente_id,)).fetchone():
            raise HTTPException(status_code=404)
        _registrar(con, cliente_id, admin, "avisa al técnico del TPV",
                   "Pendiente: el canal con el fabricante del TPV se conectará en la fase 4.")
    return RedirectResponse(f"/admin/clientes/{cliente_id}?hecho=tecnico", status_code=303)


@router.post("/clientes/{cliente_id}/plan")
async def cambiar_plan(request: Request, cliente_id: UUID):
    admin = admin_actual(request, solo_admin=True)
    datos = await comprobar_formulario(request)
    with _bd(request).conexion(plataforma=True) as con:
        if not con.execute("SELECT 1 FROM planes WHERE codigo = %s", (datos.get("plan"),)).fetchone():
            raise HTTPException(status_code=400, detail="Plan desconocido.")
        if con.execute("UPDATE clientes SET plan = %s WHERE id = %s", (datos["plan"], cliente_id)).rowcount == 0:
            raise HTTPException(status_code=404)
        _registrar(con, cliente_id, admin, "cambia de plan", datos["plan"])
    return RedirectResponse(f"/admin/clientes/{cliente_id}?hecho=plan", status_code=303)


@router.post("/clientes/{cliente_id}/modulos")
async def cambiar_modulos(request: Request, cliente_id: UUID):
    admin = admin_actual(request, solo_admin=True)
    datos = await comprobar_formulario(request)
    elegidos = {k.removeprefix("modulo_") for k in datos if k.startswith("modulo_")}
    with _bd(request).conexion(plataforma=True) as con:
        if not con.execute("SELECT 1 FROM clientes WHERE id = %s", (cliente_id,)).fetchone():
            raise HTTPException(status_code=404)
        de_pago = {m["codigo"] for m in con.execute("SELECT codigo FROM modulos WHERE NOT incluido").fetchall()}
        elegidos &= de_pago
        con.execute("DELETE FROM modulos_contratados WHERE cliente_id = %s AND NOT (modulo = ANY(%s))", (cliente_id, list(elegidos)))
        for m in elegidos:
            con.execute("INSERT INTO modulos_contratados (cliente_id, modulo) VALUES (%s, %s) ON CONFLICT DO NOTHING", (cliente_id, m))
        _registrar(con, cliente_id, admin, "cambia módulos", ", ".join(sorted(elegidos)) or "ninguno")
    return RedirectResponse(f"/admin/clientes/{cliente_id}?hecho=modulos", status_code=303)


@router.post("/clientes/{cliente_id}/conector")
async def crear_conector(request: Request, cliente_id: UUID):
    admin = admin_actual(request, solo_admin=True)
    datos = await comprobar_formulario(request)
    token = seguridad.nuevo_token_conector()
    with _bd(request).conexion(plataforma=True) as con:
        if not con.execute("SELECT 1 FROM clientes WHERE id = %s", (cliente_id,)).fetchone():
            raise HTTPException(status_code=404)
        con.execute("INSERT INTO conectores (cliente_id, tpv, hash_token) VALUES (%s, %s, %s)",
                    (cliente_id, str(datos.get("tpv", "DSTNet"))[:40], seguridad.resumen_token(token)))
        _registrar(con, cliente_id, admin, "crea un conector")
    # El token solo se enseña esta vez: no se guarda en claro en ningún sitio.
    return pagina(request, "admin_token.html", admin=admin, seccion="clientes", cliente_id=cliente_id, token=token)


# ---------- Alta ----------

@router.get("/alta")
def alta(request: Request):
    admin = admin_actual(request)
    with _bd(request).conexion(plataforma=True) as con:
        planes = con.execute("SELECT * FROM planes ORDER BY precio_eur").fetchall()
    return pagina(request, "admin_alta.html", admin=admin, seccion="alta", planes=planes, error=None, datos={})


@router.post("/alta")
async def alta_guardar(request: Request):
    admin = admin_actual(request)
    datos = await comprobar_formulario(request)
    with _bd(request).conexion(plataforma=True) as con:
        planes = con.execute("SELECT * FROM planes ORDER BY precio_eur").fetchall()

    def error(texto):
        return pagina(request, "admin_alta.html", admin=admin, seccion="alta", planes=planes, error=texto, datos=datos)

    campos = {k: str(datos.get(k, "")).strip() for k in ("nombre", "municipio", "contacto", "movil", "plan", "locales", "tpv")}
    if not all(campos[k] for k in ("nombre", "municipio", "contacto", "movil")):
        return error("Rellena nombre, municipio, persona de contacto y móvil.")
    movil = seguridad.normalizar_movil(campos["movil"])
    if not movil:
        return error("El móvil no es válido. Escríbelo sin espacios, por ejemplo 612345678.")
    if campos["plan"] not in {p["codigo"] for p in planes}:
        return error("Elige un plan.")
    if datos.get("rgpd") != "si":
        return error("Sin el contrato de protección de datos firmado no se puede dar de alta.")
    n_locales = int(campos["locales"]) if campos["locales"].isdigit() and 1 <= int(campos["locales"]) <= 50 else None
    if n_locales is None:
        return error("El número de locales debe estar entre 1 y 50.")

    hoy = date.today()
    with _bd(request).conexion(plataforma=True) as con:
        if con.execute("SELECT 1 FROM personas WHERE movil = %s", (movil,)).fetchone():
            return error("Ese móvil ya está dado de alta en otro cliente.")
        cliente_id = con.execute(
            "INSERT INTO clientes (nombre, municipio, contacto_nombre, contacto_movil, plan, estado, prueba_hasta, rgpd_firmado_en) "
            "VALUES (%s, %s, %s, %s, %s, 'prueba', %s, now()) RETURNING id",
            (campos["nombre"], campos["municipio"], campos["contacto"], movil, campos["plan"],
             sumar_meses(hoy, DURACION_PRUEBA_MESES))).fetchone()["id"]
        for i in range(n_locales):
            nombre = campos["nombre"] if n_locales == 1 else f"{campos['nombre']} {i + 1}"
            con.execute("INSERT INTO locales (cliente_id, nombre, municipio, tpv) VALUES (%s, %s, %s, %s)",
                        (cliente_id, nombre, campos["municipio"], campos["tpv"] or "DSTNet"))
        con.execute("INSERT INTO personas (cliente_id, nombre, movil, rol) VALUES (%s, %s, %s, 'dueno')",
                    (cliente_id, campos["contacto"], movil))
        _registrar(con, cliente_id, admin, "da de alta el cliente", f"prueba hasta {sumar_meses(hoy, DURACION_PRUEBA_MESES)}")
    return RedirectResponse(f"/admin/clientes/{cliente_id}?hecho=alta", status_code=303)


# ---------- Conectores ----------

@router.get("/conectores")
def conectores(request: Request):
    admin = admin_actual(request)
    with _bd(request).conexion(plataforma=True) as con:
        filas = con.execute(
            "SELECT k.*, c.nombre AS cliente, c.id AS cliente_id, "
            "(coalesce(k.ultimo_envio, k.creado_en) < now() - interval '24 hours') AS sin_datos "
            "FROM conectores k JOIN clientes c ON c.id = k.cliente_id ORDER BY sin_datos DESC, c.nombre").fetchall()
    return pagina(request, "admin_conectores.html", admin=admin, seccion="conectores", conectores=filas)


@router.get("/planes")
def planes(request: Request):
    admin = admin_actual(request)
    with _bd(request).conexion(plataforma=True) as con:
        planes = con.execute("SELECT * FROM planes ORDER BY precio_eur").fetchall()
        modulos = con.execute("SELECT * FROM modulos ORDER BY orden").fetchall()
    return pagina(request, "admin_planes.html", admin=admin, seccion="planes", planes=planes, modulos=modulos)
