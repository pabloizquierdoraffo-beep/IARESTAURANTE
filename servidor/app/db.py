"""Conexiones a la base de datos, siempre con el cliente fijado.

Toda consulta pasa por `conexion()`. Si se abre para un cliente, la base de datos solo deja
ver y tocar sus filas. Si se abre como plataforma (nosotros), se ven todos.
"""

from contextlib import contextmanager
from typing import Iterator
from uuid import UUID

import psycopg
from psycopg.rows import dict_row


class BaseDatos:
    def __init__(self, url: str):
        self.url = url

    @contextmanager
    def conexion(self, cliente_id: UUID | str | None = None, plataforma: bool = False) -> Iterator[psycopg.Connection]:
        with psycopg.connect(self.url, row_factory=dict_row) as con:
            with con.transaction():
                # set_config(..., true) solo dura esta transacción.
                con.execute("SELECT set_config('app.cliente_id', %s, true)", (str(cliente_id) if cliente_id else "",))
                con.execute("SELECT set_config('app.es_plataforma', %s, true)", ("si" if plataforma else "",))
                yield con
