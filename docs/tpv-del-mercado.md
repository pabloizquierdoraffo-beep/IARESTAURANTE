# Programas de caja (TPV) del mercado: cómo conectarlos

> Revisado el 28 de septiembre de 2026 con búsquedas en internet. Desde nuestro entorno de
> trabajo **no se pudieron abrir las webs de los fabricantes**, así que lo que viene aquí
> sale de los resultados de búsqueda y de las webs de sus distribuidores.
> **Todo lo marcado «sin confirmar» hay que preguntarlo al fabricante.** Decisión tomada:
> **solo conexión automática** (no se aceptan archivos exportados a mano).

## Resumen

| TPV | ¿Dice tener API o integraciones? | ¿Datos en el local o en la nube? | Siguiente paso |
|---|---|---|---|
| **TPV actual** (copia «Central 10.2.3») | Sí («integración oficial», somos partners) | En el local (SQL Server) | Pedir la documentación ([correo](correo-fabricante-tpv.md)) |
| **Ágora** | **Sí**: API para ERP, contabilidad, PMS y e-commerce; tiene partners de gestión (Gstock, tSpoonLab) | Sin confirmar | Pedir acceso a la API de partners |
| **Hiopos** | **Sí**: integraciones con Uber Eats, Glovo, Deliverect y FrontHotel. Tiene versión «Hiopos Cloud» | Tiene versión en la nube; sin confirmar para todos los clientes | Preguntar si hay API de ventas para terceros |
| **Numier** | **Sí**: «API de integraciones» que conecta las ventas con programas externos | Sin confirmar | Pedir la documentación de la API |
| **BDP** | Dice integrarse con ERP, CRM y e-commerce; **no se encontró una API pública** | Sin confirmar | Preguntar cómo se integran los ERP |
| **Firesoft** | **No se encontró** información de API | Sin confirmar | Preguntar al fabricante |
| **Soltac** | **No se encontró** información de API | Sin confirmar | Preguntar al fabricante |
| **«Ticsy»** | Hay un TPV llamado **Ticksy** (ticksy.app) con integraciones; **hay que confirmar que es el mismo** | Sin confirmar | Confirmar el nombre y preguntar |

## Qué significa para nosotros

- **Ágora, Hiopos y Numier** anuncian API: son los candidatos más fáciles después del TPV actual.
- Para **BDP, Firesoft, Soltac y Ticksy** no hay información pública. Hay que preguntarles
  directamente. Si no ofrecen una integración oficial, **no nos conectaremos** a escondidas a su
  base de datos: la regla es usar solo la vía oficial.
- Si un TPV guarda los datos **en la nube**, no hará falta instalar nada en el bar: nuestro
  servidor le pedirá las ventas directamente. Si los guarda **en el local**, se instala el conector.
- Nuestra plataforma está pensada para ambos casos: cada TPV es un **adaptador** que se añade sin
  tocar lo demás (ver [arquitectura](arquitectura-multi-tpv-y-modulos.md)).

## Qué preguntar a cada fabricante

Se puede reutilizar el [correo para el fabricante](correo-fabricante-tpv.md), añadiendo:
1. ¿Tenéis **API o programa de partners** para leer ventas, artículos, familias, comensales,
   stock y compras?
2. ¿Los datos están **en el ordenador del local, en vuestra nube o en ambos**?
3. ¿Cuánto cuesta el acceso y qué condiciones tiene?
4. ¿Hay **entorno de pruebas**?

## Fuentes

- Ágora: [Integraciones de software TPV | Ágora](https://www.agorapos.com/integraciones/)
- Hiopos: [Integraciones HIOPOS (Bivium)](https://bivium.es/integraciones-hiopos/),
  [Módulo integración HioPOS con Uber Eats](https://tpvhiopos.es/modulos-adicionales-para-restaurantes/81-modulo-integracion-hiopos-con-uber-eats.html),
  [Hiopos Cloud (iNet Talavera)](https://www.inet-talavera.es/productos/hiopos-cloud/bares-restaurantes)
- Numier: [Numier](https://numier.com/),
  [¿Numier ofrece integraciones con herramientas de contabilidad?](https://numier.com/numier-ofrece-integraciones-con-herramientas-de-contabilidad/)
- BDP: [BDP software (softwaredoit)](https://www.softwaredoit.es/bdp-software/bdp-software.html),
  [Software TPV BDP (tpvcenter)](https://www.tpvcenter.com/software-tpv/software-tpv-bdp-hosteleria-comercio/)
- Firesoft: [FireSoft Hostelería](https://firesoft.es/hosteleria)
- Soltac: [Software TPV para Hostelería – Soltac](https://soltac.es/hosteleria.php)
- Ticksy: [Ticksy](https://ticksy.app/)
