"""Pantallas del bar: el dueño (móvil) y los empleados. Acceso con el móvil y un código."""

from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from . import seguridad
from .comun import MOTIVOS, comprobar_formulario, entender_aviso, lunes_de, pagina

router = APIRouter()

CODIGOS_POR_CUARTO_DE_HORA = 3


class NecesitaEntrar(Exception):
    pass


def _bd(request: Request):
    return request.app.state.bd


def persona_actual(request: Request, solo_dueno: bool = False) -> dict:
    bar = request.session.get("bar")
    if not bar:
        raise NecesitaEntrar()
    if solo_dueno and bar["rol"] != "dueno":
        raise HTTPException(status_code=403, detail="Esta pantalla es solo para el dueño o encargado.")
    return bar


def _locales(request: Request, bar: dict) -> list[dict]:
    with _bd(request).conexion(bar["cliente_id"]) as con:
        return con.execute("SELECT id, nombre, es_ejemplo FROM locales ORDER BY nombre").fetchall()


def _local_elegido(request: Request, bar: dict, pedido: str | None) -> tuple[dict, list[dict]]:
    """Devuelve el local pedido (o el último usado) y la lista de locales del cliente.

    Si el local pedido no es de este cliente, la base de datos no lo devuelve y se responde
    «no encontrado»: un bar nunca puede ver otro local aunque cambie la dirección a mano.
    """
    locales = _locales(request, bar)
    if not locales:
        raise HTTPException(status_code=404, detail="Este cliente no tiene locales.")
    buscado = pedido or request.session.get("local_id")
    if buscado:
        elegido = next((l for l in locales if str(l["id"]) == str(buscado)), None)
        if elegido is None:
            if pedido:
                raise HTTPException(status_code=404, detail="Local no encontrado.")
            elegido = locales[0]
    else:
        elegido = locales[0]
    request.session["local_id"] = str(elegido["id"])
    return elegido, locales


# ---------- Acceso ----------

@router.get("/")
def portada(request: Request):
    return pagina(request, "portada.html")


@router.get("/entrar")
def entrar(request: Request):
    return pagina(request, "bar_entrar.html", error=None)


@router.post("/entrar")
async def entrar_enviar(request: Request):
    datos = await comprobar_formulario(request)
    movil = seguridad.normalizar_movil(str(datos.get("movil", "")))
    if not movil:
        return pagina(request, "bar_entrar.html", error="Ese número no parece un móvil. Escríbelo sin espacios, por ejemplo 612345678.")

    config = request.app.state.config
    with _bd(request).conexion() as con:
        encontrada = con.execute("SELECT * FROM buscar_persona_por_movil(%s)", (movil,)).fetchone()
        if encontrada:
            recientes = con.execute(
                "SELECT count(*) AS n FROM codigos_acceso WHERE persona_id = %s AND creado_en > now() - interval '15 minutes'",
                (encontrada["persona_id"],)).fetchone()["n"]
            if recientes < CODIGOS_POR_CUARTO_DE_HORA:
                codigo = seguridad.nuevo_codigo()
                con.execute(
                    "INSERT INTO codigos_acceso (persona_id, hash_codigo, caduca_en) VALUES (%s, %s, %s)",
                    (encontrada["persona_id"],
                     seguridad.resumen_codigo(config.clave_secreta, str(encontrada["persona_id"]), codigo),
                     seguridad.caducidad_codigo()))
                request.app.state.mensajeria.enviar_codigo(movil, codigo)
    # Se contesta igual exista o no el número, para no desvelar quién es cliente.
    request.session["movil_pendiente"] = movil
    return RedirectResponse("/entrar/codigo", status_code=303)


@router.get("/entrar/codigo")
def entrar_codigo(request: Request):
    movil = request.session.get("movil_pendiente")
    if not movil:
        return RedirectResponse("/entrar", status_code=303)
    codigo_prueba = None
    if request.app.state.config.modo_desarrollo:
        codigo_prueba = getattr(request.app.state.mensajeria, "ultimo_codigo", {}).get(movil)
    return pagina(request, "bar_codigo.html", movil=movil, codigo_prueba=codigo_prueba, error=None)


@router.post("/entrar/codigo")
async def entrar_codigo_comprobar(request: Request):
    datos = await comprobar_formulario(request)
    movil = request.session.get("movil_pendiente")
    if not movil:
        return RedirectResponse("/entrar", status_code=303)
    escrito = "".join(c for c in str(datos.get("codigo", "")) if c.isdigit())
    config = request.app.state.config
    error = "El código no es correcto o ha caducado. Pide uno nuevo."

    with _bd(request).conexion() as con:
        encontrada = con.execute("SELECT * FROM buscar_persona_por_movil(%s)", (movil,)).fetchone()
        codigo = None
        if encontrada:
            codigo = con.execute(
                "SELECT * FROM codigos_acceso WHERE persona_id = %s AND NOT usado AND caduca_en > now() "
                "ORDER BY creado_en DESC LIMIT 1", (encontrada["persona_id"],)).fetchone()
        if codigo and codigo["intentos"] >= seguridad.INTENTOS_MAXIMOS:
            error = "Demasiados intentos. Pide un código nuevo."
        elif codigo:
            esperado = seguridad.resumen_codigo(config.clave_secreta, str(encontrada["persona_id"]), escrito)
            if seguridad.iguales(esperado, codigo["hash_codigo"]):
                con.execute("UPDATE codigos_acceso SET usado = true WHERE id = %s", (codigo["id"],))
                persona = None
                with _bd(request).conexion(encontrada["cliente_id"]) as con2:
                    persona = con2.execute("SELECT id, nombre, rol FROM personas WHERE id = %s",
                                           (encontrada["persona_id"],)).fetchone()
                request.session.clear()
                request.session["bar"] = {
                    "persona_id": str(persona["id"]), "cliente_id": str(encontrada["cliente_id"]),
                    "rol": persona["rol"], "nombre": persona["nombre"],
                }
                return RedirectResponse("/semana" if persona["rol"] == "dueno" else "/empleado", status_code=303)
            con.execute("UPDATE codigos_acceso SET intentos = intentos + 1 WHERE id = %s", (codigo["id"],))
    return pagina(request, "bar_codigo.html", movil=movil, codigo_prueba=None, error=error)


@router.get("/salir")
def salir(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


# ---------- Dueño ----------

@router.get("/semana")
def semana(request: Request, local: str | None = None):
    bar = persona_actual(request, solo_dueno=True)
    elegido, locales = _local_elegido(request, bar, local)
    hoy = date.today()
    with _bd(request).conexion(bar["cliente_id"]) as con:
        prevision = con.execute(
            "SELECT * FROM previsiones_semana WHERE local_id = %s AND semana_inicio >= %s "
            "ORDER BY semana_inicio LIMIT 1", (elegido["id"], lunes_de(hoy))).fetchone()
    return pagina(request, "bar_semana.html", bar=bar, local=elegido, locales=locales, prevision=prevision,
                  seccion="semana", ruta="/semana")


def _dias_para_avisar() -> list[date]:
    hoy = date.today()
    return [hoy + timedelta(days=i) for i in range(14)]


@router.get("/avisar")
def avisar(request: Request, fecha: str | None = None):
    bar = persona_actual(request, solo_dueno=True)
    elegido, locales = _local_elegido(request, bar, None)
    dias = _dias_para_avisar()
    elegida = next((d for d in dias if d.isoformat() == fecha), None)
    return pagina(request, "bar_avisar.html", bar=bar, local=elegido, locales=locales, dias=dias,
                  fecha=elegida, motivos=MOTIVOS, seccion="avisar", ruta="/avisar")


def _confirmar(request: Request, bar, elegido, locales, fecha: date | None, motivo: str, personas, texto: str | None):
    return pagina(request, "bar_avisar_confirmar.html", bar=bar, local=elegido, locales=locales,
                  dias=_dias_para_avisar(), fecha=fecha, motivo=motivo, personas=personas, texto=texto,
                  motivos=MOTIVOS, seccion="avisar", ruta="/avisar")


@router.post("/avisar/preparar")
async def avisar_preparar(request: Request):
    bar = persona_actual(request, solo_dueno=True)
    datos = await comprobar_formulario(request)
    elegido, locales = _local_elegido(request, bar, None)
    fecha = next((d for d in _dias_para_avisar() if d.isoformat() == datos.get("fecha")), None)
    motivo = datos.get("motivo") if datos.get("motivo") in MOTIVOS else "Otra cosa"
    return _confirmar(request, bar, elegido, locales, fecha, motivo, None, None)


@router.post("/avisar/escrito")
async def avisar_escrito(request: Request):
    bar = persona_actual(request, solo_dueno=True)
    datos = await comprobar_formulario(request)
    elegido, locales = _local_elegido(request, bar, None)
    texto = str(datos.get("texto", "")).strip()[:500]
    if not texto:
        return RedirectResponse("/avisar", status_code=303)
    entendido = entender_aviso(texto, _dias_para_avisar())
    return _confirmar(request, bar, elegido, locales, entendido["fecha"], entendido["motivo"], entendido["personas"], texto)


@router.post("/avisar/guardar")
async def avisar_guardar(request: Request):
    bar = persona_actual(request, solo_dueno=True)
    datos = await comprobar_formulario(request)
    elegido, locales = _local_elegido(request, bar, None)
    fecha = next((d for d in _dias_para_avisar() if d.isoformat() == datos.get("fecha")), None)
    if fecha is None:
        return _confirmar(request, bar, elegido, locales, None, str(datos.get("motivo", "Otra cosa")), None, datos.get("texto"))
    personas = str(datos.get("personas", "")).strip()
    with _bd(request).conexion(bar["cliente_id"]) as con:
        con.execute(
            "INSERT INTO avisos (cliente_id, local_id, persona_id, fecha, motivo, personas, texto_libre) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (bar["cliente_id"], elegido["id"], bar["persona_id"], fecha, str(datos.get("motivo", "Otra cosa"))[:80],
             int(personas) if personas.isdigit() else None, (datos.get("texto") or None)))
    return pagina(request, "bar_avisar_hecho.html", bar=bar, local=elegido, locales=locales, fecha=fecha,
                  seccion="avisar", ruta="/avisar")


@router.get("/ahorro")
def ahorro(request: Request):
    bar = persona_actual(request, solo_dueno=True)
    elegido, locales = _local_elegido(request, bar, None)
    return pagina(request, "bar_ahorro.html", bar=bar, local=elegido, locales=locales, seccion="ahorro", ruta="/ahorro")


def _modulos(request: Request, bar: dict) -> list[dict]:
    with _bd(request).conexion(bar["cliente_id"]) as con:
        return con.execute(
            "SELECT m.codigo, m.nombre, m.descripcion, m.incluido, (mc.modulo IS NOT NULL) AS contratado "
            "FROM modulos m LEFT JOIN modulos_contratados mc ON mc.modulo = m.codigo ORDER BY m.orden").fetchall()


@router.get("/modulos")
def modulos(request: Request):
    bar = persona_actual(request, solo_dueno=True)
    elegido, locales = _local_elegido(request, bar, None)
    return pagina(request, "bar_modulos.html", bar=bar, local=elegido, locales=locales, modulos=_modulos(request, bar),
                  pedido=request.query_params.get("pedido"), seccion="modulos", ruta="/modulos")


@router.post("/modulos/informacion")
async def modulos_informacion(request: Request):
    bar = persona_actual(request, solo_dueno=True)
    datos = await comprobar_formulario(request)
    codigo = str(datos.get("modulo", ""))
    if codigo not in {m["codigo"] for m in _modulos(request, bar)}:
        raise HTTPException(status_code=404)
    with _bd(request).conexion(bar["cliente_id"]) as con:
        con.execute("INSERT INTO registro_acciones (cliente_id, quien, accion, detalle) VALUES (%s, %s, %s, %s)",
                    (bar["cliente_id"], bar["nombre"], "pide información de un módulo", codigo))
    return RedirectResponse(f"/modulos?pedido={codigo}", status_code=303)


@router.get("/ayuda")
def ayuda(request: Request):
    bar = persona_actual(request)
    config = request.app.state.config
    return pagina(request, "bar_ayuda.html", bar=bar, soporte_nombre=config.soporte_nombre,
                  soporte_telefono=config.soporte_telefono, seccion="ayuda", ruta="/ayuda")


# ---------- Empleado ----------

@router.get("/empleado")
def empleado(request: Request):
    bar = persona_actual(request)
    with _bd(request).conexion(bar["cliente_id"]) as con:
        cliente = con.execute("SELECT nombre, es_ejemplo FROM clientes").fetchone()
        permitidos = con.execute(
            "SELECT m.nombre FROM permisos p JOIN modulos m ON m.codigo = p.modulo "
            "JOIN modulos_contratados mc ON mc.modulo = p.modulo WHERE p.persona_id = %s ORDER BY m.orden",
            (UUID(bar["persona_id"]),)).fetchall()
    return pagina(request, "empleado.html", bar=bar, cliente=cliente, permitidos=permitidos, seccion="empleado")
