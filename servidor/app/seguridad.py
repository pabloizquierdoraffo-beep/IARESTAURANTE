"""Contraseñas, doble verificación, códigos por móvil y tokens del conector."""

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

_hasher = PasswordHasher()

DURACION_CODIGO = timedelta(minutes=10)
INTENTOS_MAXIMOS = 5


def hash_contrasena(contrasena: str) -> str:
    return _hasher.hash(contrasena)


def comprobar_contrasena(hash_guardado: str, contrasena: str) -> bool:
    try:
        return _hasher.verify(hash_guardado, contrasena)
    except VerificationError:
        return False


def nuevo_secreto_totp() -> str:
    return pyotp.random_base32()


def comprobar_totp(secreto: str, codigo: str) -> bool:
    return pyotp.TOTP(secreto).verify(codigo.strip(), valid_window=1)


def normalizar_movil(texto: str) -> str | None:
    """Deja el móvil como +34XXXXXXXXX. Devuelve None si no parece un móvil."""
    digitos = re.sub(r"[^\d+]", "", texto)
    if digitos.startswith("00"):
        digitos = "+" + digitos[2:]
    if re.fullmatch(r"[6789]\d{8}", digitos):
        digitos = "+34" + digitos
    return digitos if re.fullmatch(r"\+\d{9,15}", digitos) else None


def nuevo_codigo() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def resumen_codigo(clave: str, persona_id: str, codigo: str) -> str:
    return hmac.new(clave.encode(), f"{persona_id}:{codigo}".encode(), hashlib.sha256).hexdigest()


def caducidad_codigo() -> datetime:
    return datetime.now(timezone.utc) + DURACION_CODIGO


def nuevo_token_conector() -> str:
    return secrets.token_urlsafe(32)


def resumen_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def nuevo_token_formulario() -> str:
    return secrets.token_urlsafe(24)


def iguales(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())
