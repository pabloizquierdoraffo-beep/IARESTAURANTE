"""Aplicación web: entrada de la plataforma (nosotros), del bar (dueño y empleados) y del conector."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from . import config as configuracion
from .comun import pagina
from .db import BaseDatos
from .mensajeria import Mensajeria, MensajeriaDesarrollo
from .rutas_admin import NecesitaEntrarAdmin
from .rutas_admin import router as router_admin
from .rutas_bar import NecesitaEntrar
from .rutas_bar import router as router_bar
from .rutas_conector import router as router_conector

CABECERAS_SEGURIDAD = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
    "Content-Security-Policy": (
        "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; img-src 'self' data:; form-action 'self'; frame-ancestors 'none'"
    ),
}


def crear_app(config: configuracion.Config | None = None, mensajeria: Mensajeria | None = None) -> FastAPI:
    config = config or configuracion.cargar()
    app = FastAPI(title="Plataforma de previsión", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.config = config
    app.state.bd = BaseDatos(config.database_url)
    app.state.mensajeria = mensajeria or MensajeriaDesarrollo()

    app.add_middleware(SessionMiddleware, secret_key=config.clave_secreta, session_cookie="sesion",
                       max_age=30 * 24 * 3600, same_site="lax", https_only=config.cookies_seguras)

    @app.middleware("http")
    async def cabeceras(request: Request, siguiente):
        respuesta = await siguiente(request)
        for clave, valor in CABECERAS_SEGURIDAD.items():
            respuesta.headers.setdefault(clave, valor)
        return respuesta

    @app.exception_handler(NecesitaEntrar)
    async def a_entrar(request: Request, _):
        return RedirectResponse("/entrar", status_code=303)

    @app.exception_handler(NecesitaEntrarAdmin)
    async def a_entrar_admin(request: Request, _):
        return RedirectResponse("/admin/entrar", status_code=303)

    @app.exception_handler(StarletteHTTPException)
    async def error_http(request: Request, error: StarletteHTTPException):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": error.detail}, status_code=error.status_code)
        textos = {404: "No encontrado.", 403: "No tienes permiso para esto."}
        detalle = error.detail if isinstance(error.detail, str) and error.detail not in ("Not Found", "Forbidden") else None
        respuesta = pagina(request, "error.html", mensaje=detalle or textos.get(error.status_code, "Algo ha fallado."))
        respuesta.status_code = error.status_code
        return respuesta

    app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")
    app.include_router(router_bar)
    app.include_router(router_admin)
    app.include_router(router_conector)
    return app
