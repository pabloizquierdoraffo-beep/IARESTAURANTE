# Cómo se conecta cualquier TPV y cómo funcionan los módulos

> Documento en español sencillo. Fecha: 28 de septiembre de 2026.

## 1. La idea en una frase

Cada programa de caja habla «su idioma». Nosotros ponemos un **traductor (adaptador)** por
cada TPV, que pasa sus datos a **un idioma común**. A partir de ahí, toda la plataforma
(previsión, mensajes y módulos) trabaja igual, venga el bar del TPV que venga.

## 2. Dibujo

```
  TPV EN EL LOCAL                         TPV EN LA NUBE
  (ej.: DSTNet, SQL Server)            (ej.: los que tienen API en internet)

  ┌─────────────┐                         ┌─────────────┐
  │ Caja del bar│                         │ Nube del TPV│
  └──────┬──────┘                         └──────┬──────┘
         │ solo lectura                          │ solo lectura, con su API oficial
  ┌──────▼──────────────┐                 ┌──────▼──────────────┐
  │ CONECTOR en el bar  │                 │ Adaptador en nuestro│
  │ + adaptador del TPV │                 │ servidor            │
  └──────┬──────────────┘                 └──────┬──────────────┘
         │   datos en el IDIOMA COMÚN            │
         └───────────────┬───────────────────────┘
                         ▼
        ┌─────────────────────────────────────────────┐
        │ NUESTRA PLATAFORMA (servidor en la UE)       │
        │                                              │
        │  NÚCLEO (todos los clientes)                 │
        │   · previsión y mensaje del lunes            │
        │   · avisos del hostelero · ahorro            │
        │                                              │
        │  MÓDULOS DE PAGO (solo si están contratados) │
        │   1 turnos según la previsión y reservas     │
        │   2 preparación y descongelación             │
        │   3 escandallos, relevé y mermas             │
        │   4 empleados: fichaje, turnos, vacaciones   │
        └─────────────────────────────────────────────┘
                         ▲
     nosotros · dueño · empleados
     móvil · ordenador · tableta (cada uno ve solo lo que le permiten)
```

## 3. El idioma común (qué datos se traducen)

Todo va **agrupado** y **sin datos personales**:

| Dato | Detalle |
|---|---|
| Ventas | Por local, día, hora y artículo: unidades e importe |
| Tickets y comensales | Por local, día y hora |
| Artículos | Código, nombre, familia y precio |
| Familias | Familia y familia principal (cervezas, refrescos, cocina…) |
| Stock y compras | Si el TPV lo tiene y el cliente tiene contratado el módulo |

Nunca se traducen: empleados, clientes, textos escritos a mano, pagos ni datos fiscales
(lista completa en [mapa-datos-tpv.md](mapa-datos-tpv.md)). El conector tiene además un
**filtro final**: si un adaptador intentara enviar un dato que no está en la lista permitida,
se bloquea.

## 4. Añadir un TPV nuevo

1. Conseguir del fabricante la **documentación oficial** y un **entorno de pruebas**.
2. Escribir su **adaptador** (su traductor al idioma común).
3. Probarlo con las mismas pruebas automáticas que el resto: totales que cuadran, nada
   personal y solo lectura.
4. Activarlo. **No hay que tocar** la previsión, los mensajes ni los módulos.

Regla: **solo por la vía oficial del fabricante**. Si un TPV no ofrece integración, no se
conecta.

## 5. Los módulos de pago

- **Núcleo:** lo tienen todos los clientes (previsión, mensaje del lunes, avisos y ahorro).
- **Módulos, en este orden:**
  1. turnos según la previsión (y según haya más o menos reservas de lo previsto);
  2. preparación y descongelación diaria;
  3. escandallos (qué lleva cada plato o bebida y cuánto cuesta), **relevé** (el escandallo
     actualizado cada día, con lo perdido y las mermas) y mermas y compras;
  4. empleados: fichaje, turnos y vacaciones.
- Del TPV se coge todo lo que haya; lo que el TPV no tenga o haga peor (por ejemplo, las
  mermas, que hoy nadie rellena) se gestiona en nuestra plataforma.
- **Cada módulo se cobra aparte** cuando el cliente lo contrata. Los precios están por decidir.
- **Permisos:** cualquier empleado puede entrar desde el móvil, el ordenador o la tableta,
  pero solo ve los módulos que tiene contratados el local y para los que tiene permiso.
- **Cuándo:** los módulos se construyen **después del MVP**. Desde ya, la base de datos tendrá
  preparadas las tablas de «módulos contratados» y «permisos» para no rehacer nada.

## 6. Un modelo común para todos los locales

La previsión se entrena como **un solo modelo con las ventas de todos los locales**, que a la
vez tiene en cuenta cómo es cada uno. Así «aprende de los demás» sin que ningún bar vea los
datos de otro. Detalle en [visión del producto](vision-producto.md).

## 7. Qué cambia respecto al plan inicial

- «Otros TPV» ya no queda fuera del MVP: **la base común entra ahora**, aunque solo se conecta
  el TPV actual en el piloto.
- Solo conexión automática: no se aceptan archivos exportados a mano.
- Se añade la hoja de ruta de módulos de pago, a construir después del MVP.
