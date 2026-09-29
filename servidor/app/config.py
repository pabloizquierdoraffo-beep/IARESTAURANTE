"""Configuración leída de variables de entorno. Ninguna contraseña va escrita en el código."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    # Conexión con el usuario de la aplicación (NO el dueño de las tablas), para que se le
    # apliquen siempre las reglas de separación de clientes.
    database_url: str
    clave_secreta: str
    # En desarrollo el código de acceso se enseña en pantalla, marcado como tal,
    # porque todavía no hay WhatsApp. En producción debe estar desactivado.
    modo_desarrollo: bool
    cookies_seguras: bool
    soporte_nombre: str
    soporte_telefono: str


def cargar() -> Config:
    clave = os.environ.get("CLAVE_SECRETA", "")
    if len(clave) < 32:
        raise RuntimeError("Falta CLAVE_SECRETA (al menos 32 caracteres).")
    return Config(
        database_url=os.environ["DATABASE_URL"],
        clave_secreta=clave,
        modo_desarrollo=os.environ.get("MODO_DESARROLLO", "0") == "1",
        cookies_seguras=os.environ.get("COOKIES_SEGURAS", "1") == "1",
        soporte_nombre=os.environ.get("SOPORTE_NOMBRE", "Soporte (ejemplo)"),
        soporte_telefono=os.environ.get("SOPORTE_TELEFONO", "600 000 000"),
    )
