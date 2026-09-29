"""Carga clientes de EJEMPLO para ver y probar la plataforma. Todo va marcado con es_ejemplo.

    DATABASE_URL=... python -m app.datos_ejemplo

Los móviles de ejemplo empiezan por +34600 00 00 (no son de nadie).
"""

import json
import os
from datetime import date, timedelta

from .comun import lunes_de, sumar_meses
from .db import BaseDatos

MOVIL_DUENO_ESQUINA = "+34600000001"
MOVIL_EMPLEADA_ESQUINA = "+34600000011"


def _prevision_ejemplo(lunes: date) -> tuple[list, list]:
    consejos = [
        {"etiqueta": "Gente", "texto": "El sábado vendrá más gente: entre 180 y 220 clientes. El martes, menos.",
         "porque": "Porque el sábado hay partido y hará 24 grados."},
        {"etiqueta": "Qué pedir", "texto": "Pide unos 2 barriles más de cerveza para el fin de semana. Refrescos y café, lo normal.",
         "porque": "Porque con calor y partido se venden más cañas por la noche."},
        {"etiqueta": "Personal", "texto": "Pon un camarero más el sábado de 20:00 a 24:00. El martes por la tarde basta con uno.",
         "porque": "Porque la noche del sábado será como el sábado del puente de mayo."},
    ]
    base = [("Nubes, 19°", "normal", 90, 110, "Más gente al mediodía"),
            ("Lluvia, 16°", "menos", 60, 80, "Tarde floja"),
            ("Sol, 21°", "normal", 90, 115, "Más gente al mediodía"),
            ("Sol, 22°", "normal", 100, 125, "Buena noche"),
            ("Sol, 23°", "mas", 150, 180, "Noche fuerte, de 21:00 a 00:00"),
            ("Sol, 24°", "mas", 180, 220, "Partido a las 21:00. Noche muy fuerte"),
            ("Sol, 22°", "mas", 130, 160, "Mediodía fuerte")]
    dias = [{"fecha": (lunes + timedelta(days=i)).isoformat(), "tiempo": t, "nivel": n, "clientes_min": a, "clientes_max": b,
             "franjas": f} for i, (t, n, a, b, f) in enumerate(base)]
    return consejos, dias


def cargar(url: str) -> None:
    hoy = date.today()
    proximo_lunes = lunes_de(hoy) + timedelta(days=7)
    bd = BaseDatos(url)
    with bd.conexion(plataforma=True) as con:
        if con.execute("SELECT 1 FROM clientes WHERE es_ejemplo LIMIT 1").fetchone():
            print("Ya hay datos de ejemplo. No se cargan otra vez.")
            return

        def cliente(nombre, municipio, plan, estado, movil, contacto, prueba_hasta=None):
            return con.execute(
                "INSERT INTO clientes (nombre, municipio, contacto_nombre, contacto_movil, plan, estado, prueba_hasta, "
                "rgpd_firmado_en, es_ejemplo) VALUES (%s, %s, %s, %s, %s, %s, %s, now(), true) RETURNING id",
                (nombre, municipio, contacto, movil, plan, estado, prueba_hasta)).fetchone()["id"]

        def local(cid, nombre, municipio, id_en_tpv):
            return con.execute(
                "INSERT INTO locales (cliente_id, nombre, municipio, tpv, id_en_tpv, es_ejemplo) "
                "VALUES (%s, %s, %s, 'DSTNet', %s, true) RETURNING id", (cid, nombre, municipio, id_en_tpv)).fetchone()["id"]

        def persona(cid, nombre, movil, rol):
            return con.execute("INSERT INTO personas (cliente_id, nombre, movil, rol, es_ejemplo) VALUES (%s, %s, %s, %s, true) "
                               "RETURNING id", (cid, nombre, movil, rol)).fetchone()["id"]

        def conector(cid, horas_desde_envio):
            con.execute("INSERT INTO conectores (cliente_id, tpv, hash_token, ultimo_envio, creado_en) "
                        "VALUES (%s, 'DSTNet', md5(random()::text), now() - make_interval(hours => %s), now() - interval '30 days')",
                        (cid, horas_desde_envio))

        def mensajes(cid, leidos, total):
            for i in range(total):
                con.execute("INSERT INTO mensajes (cliente_id, tipo, enviado_en, leido_en) VALUES "
                            "(%s, 'lunes', now() - make_interval(days => %s), CASE WHEN %s THEN now() - make_interval(days => %s) END)",
                            (cid, 7 * i, i < leidos, 7 * i))

        def modulos(cid, *codigos):
            for c in codigos:
                con.execute("INSERT INTO modulos_contratados (cliente_id, modulo) VALUES (%s, %s)", (cid, c))

        # Bar La Esquina: 2 locales, dueño y una empleada. Es el que se usa para probar la entrada del bar.
        esquina = cliente("Bar La Esquina (ejemplo)", "Sevilla", "estandar", "activo", MOVIL_DUENO_ESQUINA, "Antonio (ejemplo)")
        l1 = local(esquina, "Bar La Esquina (ejemplo)", "Sevilla", "1-1")
        local(esquina, "La Esquina Playa (ejemplo)", "Sevilla", "1-2")
        persona(esquina, "Antonio (ejemplo)", MOVIL_DUENO_ESQUINA, "dueno")
        laura = persona(esquina, "Laura (ejemplo)", MOVIL_EMPLEADA_ESQUINA, "empleado")
        conector(esquina, 6)
        mensajes(esquina, 4, 4)
        modulos(esquina, "turnos", "empleados")
        con.execute("INSERT INTO permisos (cliente_id, persona_id, modulo) VALUES (%s, %s, 'empleados')", (esquina, laura))
        consejos, dias = _prevision_ejemplo(proximo_lunes)
        con.execute("INSERT INTO previsiones_semana (cliente_id, local_id, semana_inicio, consejos, dias, es_ejemplo) "
                    "VALUES (%s, %s, %s, %s, %s, true)", (esquina, l1, proximo_lunes, json.dumps(consejos), json.dumps(dias)))

        grifo = cliente("Cervecería El Grifo (ejemplo)", "Málaga", "basico", "activo", "+34600000002", "Rosa (ejemplo)")
        local(grifo, "Cervecería El Grifo (ejemplo)", "Málaga", "1-1")
        persona(grifo, "Rosa (ejemplo)", "+34600000002", "dueno")
        conector(grifo, 8)
        mensajes(grifo, 0, 3)

        arcos = cliente("Taberna Los Arcos (ejemplo)", "Córdoba", "estandar", "activo", "+34600000003", "Manuel (ejemplo)")
        local(arcos, "Taberna Los Arcos (ejemplo)", "Córdoba", "1-1")
        persona(arcos, "Manuel (ejemplo)", "+34600000003", "dueno")
        conector(arcos, 72)
        mensajes(arcos, 3, 4)
        modulos(arcos, "turnos")

        plaza = cliente("Café Plaza (ejemplo)", "Granada", "basico", "prueba", "+34600000004", "Lucía (ejemplo)",
                        hoy + timedelta(days=4))
        local(plaza, "Café Plaza (ejemplo)", "Granada", "1-1")
        persona(plaza, "Lucía (ejemplo)", "+34600000004", "dueno")
        conector(plaza, 5)
        mensajes(plaza, 2, 2)

        marisma = cliente("Grupo Marisma (ejemplo)", "Cádiz", "grupo", "activo", "+34600000005", "Paco (ejemplo)")
        for i in range(1, 4):
            local(marisma, f"Marisma {i} (ejemplo)", "Cádiz", f"1-{i}")
        persona(marisma, "Paco (ejemplo)", "+34600000005", "dueno")
        conector(marisma, 7)
        mensajes(marisma, 4, 4)
        modulos(marisma, "turnos", "preparacion", "escandallos", "empleados")

        telmo = cliente("Bodega San Telmo (ejemplo)", "Jerez", "estandar", "prueba", "+34600000006", "Carmen (ejemplo)",
                        sumar_meses(hoy, 2) - timedelta(days=50))
        local(telmo, "Bodega San Telmo (ejemplo)", "Jerez", "1-1")
        persona(telmo, "Carmen (ejemplo)", "+34600000006", "dueno")
    print("Datos de ejemplo cargados. Dueño de prueba: 600 000 001. Empleada de prueba: 600 000 011.")


if __name__ == "__main__":
    cargar(os.environ["DATABASE_URL"])
