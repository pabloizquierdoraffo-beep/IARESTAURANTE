"""Envío de mensajes al hostelero.

De momento solo existe el envío de desarrollo: guarda el último código en memoria para
enseñarlo en pantalla (marcado como prueba). El envío por WhatsApp (con SMS de reserva)
llegará en la fase 4, detrás de esta misma interfaz.
"""

from typing import Protocol


class Mensajeria(Protocol):
    def enviar_codigo(self, movil: str, codigo: str) -> None: ...
    def enviar_texto(self, movil: str, texto: str) -> None: ...


class MensajeriaDesarrollo:
    def __init__(self) -> None:
        self.ultimo_codigo: dict[str, str] = {}
        self.enviados: list[tuple[str, str]] = []

    def enviar_codigo(self, movil: str, codigo: str) -> None:
        self.ultimo_codigo[movil] = codigo

    def enviar_texto(self, movil: str, texto: str) -> None:
        self.enviados.append((movil, texto))
