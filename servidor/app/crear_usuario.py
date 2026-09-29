"""Crea un usuario de la plataforma (nosotros) y muestra la clave para la app de verificación.

    DATABASE_URL=... python -m app.crear_usuario correo@empresa.es admin|comercial

Pide la contraseña sin mostrarla. Al terminar enseña un enlace «otpauth://» y una clave para
añadir la cuenta a una app de verificación (Google Authenticator, Microsoft Authenticator…).
"""

import getpass
import os
import sys

import pyotp

from . import seguridad
from .db import BaseDatos


def crear(url: str, email: str, rol: str, contrasena: str) -> str:
    if rol not in ("admin", "comercial"):
        raise ValueError("El rol debe ser admin o comercial.")
    if len(contrasena) < 12:
        raise ValueError("La contraseña debe tener al menos 12 caracteres.")
    secreto = seguridad.nuevo_secreto_totp()
    with BaseDatos(url).conexion(plataforma=True) as con:
        con.execute("INSERT INTO usuarios_plataforma (email, hash_contrasena, totp_secreto, rol) VALUES (%s, %s, %s, %s)",
                    (email.strip().lower(), seguridad.hash_contrasena(contrasena), secreto, rol))
    return secreto


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    correo, rol = sys.argv[1], sys.argv[2]
    contrasena = getpass.getpass("Contraseña (mínimo 12 caracteres): ")
    secreto = crear(os.environ["DATABASE_URL"], correo, rol, contrasena)
    print("Usuario creado. Añádelo a tu app de verificación con esta clave:", secreto)
    print(pyotp.TOTP(secreto).provisioning_uri(name=correo, issuer_name="Plataforma de previsión"))
