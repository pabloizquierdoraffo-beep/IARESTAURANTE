# Qué hay en la copia de prueba del TPV y qué datos usaremos

> Revisado el 28 de septiembre de 2026 con la copia `Central_10.2.3_24092026_1039.bak`.
> **La copia no se ha subido a GitHub** ni a ningún otro sitio: se abrió solo en un
> ordenador de pruebas temporal.

## 1. Qué contiene la copia

| Dato | Valor |
|---|---|
| Tipo de archivo | Un archivo comprimido (7-Zip) con dentro una copia de SQL Server llamada «Central» |
| Tablas | 327 (casi todas vacías) |
| Locales dados de alta | 2 |
| Ventas | **1 solo día (27 de junio de 2026), de 9:29 a 12:52** |
| Tickets | 27, con un total de **84,50 €** |
| Líneas de venta | 33 (más 13 anuladas y 10 borradas, que van en otras tablas) |
| Mermas registradas | 0 |
| Datos personales en los tickets (nombre, teléfono, NIF, dirección) | Ninguno relleno en esta copia |

**Conclusión:** esta copia sirve para **entender cómo guarda los datos el TPV**, pero
**no sirve para entrenar la previsión**. Para eso hace falta la copia de un bar con
**al menos 12 meses** de ventas, como ya sabíamos. Con un solo día (y solo de mañana) no
se puede saber si un sábado se vende más que un martes ni cómo afecta el calor.

## 2. Lo que sí hemos aprendido

- **Cada línea de venta** trae el local, la fecha y la hora exactas, el artículo, su
  nombre, la cantidad, el precio por unidad (con IVA) y la familia.
  Se ha comprobado que la suma de las líneas coincide con el total de los tickets (84,50 €).
- **Cada ticket** trae el **número de comensales** (`TableMembers`). Esto es muy útil para
  dar al hostelero el **rango de clientes** del día.
- **Las familias** están en dos niveles: una familia principal (BEBIDAS, CAFETERÍA,
  ENTRANTES, CARNES/AVES…) y una familia concreta (CERVEZAS NACIONALES, COMBINADOS,
  REFRESCOS, CAFÉS…). Con eso podemos hacer los grupos que pide el encargo: cervezas,
  refrescos, combinados, cocina…
- **Las mermas** están en una tabla aparte (`WastedSalesOrderLine`). En esta copia está
  vacía; hay que ver si los bares reales la rellenan (duda 7 del plan).
- **Stock y compras** están en `StockMutation`, `ArticleStock` y `ArticlePurchase`.

## 3. Qué datos enviará el conector (y cuáles nunca)

### Enviará, **agrupados por local, día, hora y artículo**
| Dato | De dónde sale |
|---|---|
| Local | `SalesOrderLine.Establishment` |
| Día y hora (sin minutos ni segundos) | `SalesOrderLine.OrderDate` |
| Artículo y su nombre | `SalesOrderLine.Article`, `Description` |
| Familia y familia principal | `TurnOverGroup`, `MainTurnOverGroup` |
| Unidades vendidas | suma de `Amount` |
| Importe vendido | suma de `Price × Amount` |
| Número de tickets y de comensales por hora | `SalesOrder` (conteo y suma de `TableMembers`) |
| Mermas por día y artículo | `WastedSalesOrderLine` (si se usa) |
| Carta y familias | `Article`, `ArticleTariff`, `TurnOverGroup`, `MainTurnOverGroup` |

### **Nunca** enviará
- **Empleados:** `Employee`, `EmployeeInvite`, `EmployeeDiscount`, `EmployeeChangePrice`
  y la tabla `Employee`.
- **Clientes:** nombre, teléfono, dirección, código postal, NIF y datos de pedidos a
  domicilio o por la web (`TeleName`, `TelePhone`, `TeleStreet1`, `Web…`, `Nif`,
  `BuyerRnc`, `ZipCode`, `CustomerNumber`…).
- **Textos libres**, que pueden contener cualquier cosa: `Observation`, `ReturnNote`,
  `DiscountReason`, `InvitationReason`, `TeleNote`.
- **Pagos y datos fiscales:** tarjetas, facturas electrónicas, números de ticket fiscal.
- Usuarios y contraseñas del propio TPV (`CentralUsers…`).

## 4. Pendiente de confirmar con el fabricante

- Que el conector pueda leer estas tablas **mediante su integración oficial** y en modo
  **solo lectura**. Aquí las hemos mirado directamente en una copia, algo que **no**
  haremos en los bares.
- Qué significan algunos campos: los tipos de línea (`LineType`), los menús y las líneas
  anuladas, para no contar ventas de más o de menos.
- Si los bares rellenan de verdad las mermas y el número de comensales.
