"""Ayudas comunes a todas las pantallas."""

import calendar
import re
from datetime import date
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates

from . import seguridad

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
MOTIVOS = ["Celebración", "Reserva grande", "Partido", "Cierre", "Otra cosa"]

plantillas = Jinja2Templates(directory=str(Path(__file__).parent / "plantillas"))


def dia_largo(d: date) -> str:
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]}"


def dia_corto(d: date) -> str:
    return f"{DIAS[d.weekday()].capitalize()} {d.day}"


def semana_titulo(lunes: date) -> str:
    domingo = date.fromordinal(lunes.toordinal() + 6)
    if lunes.month == domingo.month:
        return f"Semana del {lunes.day} al {domingo.day} de {MESES[domingo.month - 1]}"
    return f"Semana del {lunes.day} de {MESES[lunes.month - 1]} al {domingo.day} de {MESES[domingo.month - 1]}"


def a_fecha(valor) -> date:
    return valor if isinstance(valor, date) else date.fromisoformat(str(valor))


def euros(valor) -> str:
    entero = f"{float(valor):,.0f}".replace(",", ".")
    return f"{entero} €"


plantillas.env.filters["dia_largo"] = dia_largo
plantillas.env.filters["dia_corto"] = dia_corto
plantillas.env.filters["euros"] = euros
plantillas.env.filters["semana_titulo"] = semana_titulo
plantillas.env.filters["a_fecha"] = a_fecha


def sumar_meses(d: date, meses: int) -> date:
    mes = d.month - 1 + meses
    anio = d.year + mes // 12
    mes = mes % 12 + 1
    return date(anio, mes, min(d.day, calendar.monthrange(anio, mes)[1]))


def lunes_de(d: date) -> date:
    return date.fromordinal(d.toordinal() - d.weekday())


# ---------- Protección de formularios ----------

def token_formulario(request: Request) -> str:
    token = request.session.get("csrf")
    if not token:
        token = seguridad.nuevo_token_formulario()
        request.session["csrf"] = token
    return token


async def comprobar_formulario(request: Request) -> dict:
    """Lee el formulario y comprueba que viene de nuestra propia página."""
    datos = dict(await request.form())
    esperado = request.session.get("csrf", "")
    if not esperado or not seguridad.iguales(esperado, str(datos.get("csrf", ""))):
        raise HTTPException(status_code=403, detail="El formulario ha caducado. Vuelve a cargar la página.")
    return datos


def pagina(request: Request, plantilla: str, **contexto):
    contexto.setdefault("csrf", token_formulario(request))
    contexto.setdefault("modo_desarrollo", request.app.state.config.modo_desarrollo)
    return plantillas.TemplateResponse(request, plantilla, contexto)


# ---------- Entender avisos escritos ----------

_COSAS = [("comunión", "Celebración (comunión)"), ("comunion", "Celebración (comunión)"), ("boda", "Celebración (boda)"),
          ("bautizo", "Celebración (bautizo)"), ("cumple", "Celebración (cumpleaños)"), ("cena de empresa", "Reserva grande"),
          ("reserva", "Reserva grande"), ("partido", "Partido"), ("cerr", "Cierre"), ("concierto", "Otra cosa (concierto)")]


def entender_aviso(texto: str, dias_posibles: list[date]) -> dict:
    """Saca día, motivo y personas de una frase como «el viernes tengo una comunión de 60».

    Siempre se le enseña al hostelero lo entendido para que lo confirme o lo cambie.
    """
    t = texto.lower()
    fecha = None
    for d in dias_posibles:
        nombre = DIAS[d.weekday()]
        if nombre in t or nombre.replace("é", "e").replace("á", "a") in t:
            fecha = d
            break
    motivo = next((m for clave, m in _COSAS if clave in t), "Otra cosa")
    numero = re.search(r"\b(\d{1,4})\b", t)
    return {"fecha": fecha, "motivo": motivo, "personas": int(numero.group(1)) if numero else None}
