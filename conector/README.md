# Conector

Programa que irá en el ordenador del bar (o en el servidor central del grupo). Lee las
ventas del programa de caja (TPV), las traduce al **idioma común** y las envía cifradas a
nuestra plataforma. **Solo lee: nunca escribe en el TPV.**

## Partes

| Carpeta | Qué es |
|---|---|
| `src/Conector.Nucleo` | Lo común a todos los TPV: el idioma común, la cola de envíos pendientes (si no hay internet) y dos barreras de seguridad |
| `src/Conector.Adaptadores.DSTNet` | El traductor de DSTNet (el primero). Cada TPV nuevo será otra carpeta como esta |
| `tests/Conector.Pruebas` | Pruebas automáticas |
| `pruebas/preparar-bd-pruebas.sh` | Prepara una copia de prueba de DSTNet con un usuario de solo lectura |

## Las barreras de seguridad

1. **Usuario de solo lectura** en la base de datos del TPV: aunque se intentara, no podría escribir.
2. **Solo consultas de lectura:** cada consulta se revisa antes de ejecutarse y se rechaza si
   contiene algo que no sea leer.
3. **Lista de campos permitidos:** antes de enviar, se comprueba que el paquete solo lleva campos
   del idioma común. Si apareciera un dato de empleados, clientes o pagos, no se envía.

## Qué comprueban las pruebas (25)

- Los totales de la copia de prueba cuadran: **84,50 €, 50 unidades, 27 tickets y 27 comensales**.
- Las ventas se reparten bien por horas (9, 10, 11 y 12 h).
- Llegan la carta y las familias (59 familias, 148 artículos y 91 precios).
- **No sale ningún dato personal.**
- **El usuario del conector no puede escribir** en el TPV (se intenta y la base de datos lo impide).
- Se rechazan las consultas que no son de lectura y los campos no permitidos.
- **Sin internet no se pierde nada:** lo pendiente se guarda y se reenvía después, en orden.
- Funciona de principio a fin: leer, guardar y enviar.
- El envío al servidor lleva el token del conector y, si el servidor falla, el paquete se queda en la cola.
- Prueba real de la caja a la plataforma (opcional, con `CONECTOR_SERVIDOR_URL` y `CONECTOR_TOKEN`).

## Cómo ejecutar las pruebas (para un programador)

```bash
# 1. Preparar la copia de prueba (la copia .bak nunca se sube al repositorio)
SA_PASSWORD='...' LECTOR_PASSWORD='...' ./pruebas/preparar-bd-pruebas.sh /ruta/a/copia.bak
export CONECTOR_BD_PRUEBAS='Server=localhost;Database=Central;User Id=conector_lector;Password=...;TrustServerCertificate=True'

# 2. Ejecutar
dotnet test
```

Sin la copia de prueba, las 6 pruebas que la necesitan se saltan y las demás se ejecutan igual.

## Qué falta

- Convertirlo en un **servicio de Windows** que arranque solo y se ejecute cada noche, y el
  aviso cuando deja de sincronizar (fase 4).
- Configurar la dirección del servidor y el token en el servicio de Windows (fase 4).
- Confirmar con DSTNet el significado de algunos campos (tipos de línea, menús, tarifas) y que
  podemos leer por su **integración oficial**.
