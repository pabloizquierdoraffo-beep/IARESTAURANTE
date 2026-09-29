# Visión del producto

> En español sencillo. Fecha: 29 de septiembre de 2026.
> Recoge lo que nos has contado; los precios y el texto comercial están pendientes.

## 1. Qué es y qué no es

- **Es** una **plataforma centralizada con IA** para bares y restaurantes: predice las ventas
  y, con esa previsión, ayuda a organizar el personal, la mercancía y los costes.
- **No es un TPV.** Las cajas ya las hacen bien otras empresas (DSTNet, Ágora, Hiopos…).
  Nosotros **leemos** sus datos y ponemos la inteligencia encima.

## 2. Lo que vendemos, en una frase

**«Te predice las ventas y aprende de muchos restaurantes, sin que nadie vea tus datos».**

> El texto comercial definitivo lo decides tú más adelante. Mientras tanto, la regla es no
> prometer ninguna mejora que no hayamos medido.

### Cómo aprende de los demás sin compartir datos
1. Cada bar envía sus ventas **agrupadas y sin datos personales** (ver
   [mapa de datos](mapa-datos-tpv.md)).
2. En nuestros servidores (en la UE) se entrena **un modelo común** con las ventas de todos
   los locales. Así aprende cosas generales, como «cuando hace calor y hay partido, se vende
   más cerveza por la noche», que un bar solo tardaría años en ver.
3. Ese modelo común se ajusta a **cómo es cada local** (su barrio, su horario, su carta).
4. **Ningún bar ve nunca los datos de otro.** Lo único que se comparte es lo aprendido, no
   las ventas.
5. **Autorización:** una cláusula clara en el contrato de todos los clientes. **Debe
   revisarla un abogado** antes de usarla.

**Importante:** esto se nota más cuantos más locales haya. En el piloto (10 locales) la
mejora por «aprender de otros» será pequeña; se medirá y se enseñará tal cual.

## 3. Quién entra y qué ve

| Usuario | Quién es | Qué hace | Dónde |
|---|---|---|---|
| **Nosotros** | Administradores, comerciales y soporte | Dar de alta clientes, contratar módulos, ver conectores y quién necesita atención | Ordenador |
| **Dueño** | Quien contrata | Ve la previsión y los consejos, contrata módulos y da permisos a sus empleados | Móvil, ordenador o tableta |
| **Empleado** | Camareros, cocina, encargados | Fichar, ver sus turnos y vacaciones y, si tiene permiso, otros módulos | Móvil, ordenador o tableta |

Cada persona **solo ve lo que su local tiene contratado y lo que le permiten**.

## 4. Qué incluye

### Núcleo (todos los clientes)
- Previsión de ventas de los 7 días siguientes, con rangos y el motivo.
- Mensaje del lunes: qué días vendrá más o menos gente, qué pedir y cuánto personal.
- Avisos del hostelero (eventos, reservas grandes…) por botón, texto o audio.
- Informe mensual del ahorro estimado.

### Módulos de pago (después del MVP, en este orden)
Cada uno se cobra aparte cuando el cliente lo contrata; los precios están por decidir.

1. **Turnos según la previsión.** Cuántas personas poner y a qué horas. Si el hostelero
   tiene **más o menos reservas** de las previstas, la recomendación se ajusta.
2. **Preparación y descongelación.** Qué sacar y descongelar cada día según lo que se espera
   vender.
3. **Escandallos, relevé y mermas.**
   - *Escandallo:* qué lleva cada plato o bebida y cuánto cuesta.
   - *Relevé:* el escandallo actualizado **cada día** para ciertos productos, con lo que se
     ha perdido y las mermas del día.
   - *Mermas y compras:* hoy nadie rellena las mermas en el TPV, así que se apuntarán en
     nuestra plataforma.
4. **Empleados: fichaje, turnos y vacaciones.** Cada empleado entra a fichar y a ver sus
   turnos y vacaciones.

Del TPV se coge **todo lo que haya** (ventas, artículos, familias, comensales, stock, compras).
Lo que el TPV no tenga o haga peor se gestiona en nuestra plataforma.

## 5. La decisión es siempre del hostelero

Todas las recomendaciones (compras, personal, preparación…) llevarán un aviso visible, por
ejemplo:

> «Es una recomendación hecha con inteligencia artificial. La decisión final es tuya.»

Esto cumple además el Reglamento europeo de IA, que obliga a indicar que el contenido lo
genera una IA. **El texto legal exacto de la limitación de responsabilidad debe redactarlo
un abogado** para el contrato y las condiciones de uso.

## 6. Notas legales que hay que tener en cuenta

- **Fichaje:** en España, el registro de la jornada es obligatorio. Los registros se guardan
  **4 años** y deben estar a disposición de los trabajadores, sus representantes y la
  Inspección de Trabajo. La normativa se ha ido actualizando, así que **antes de programar
  este módulo lo revisaremos con un asesor laboral** para cumplir la versión vigente.
- **Datos de empleados:** nombres, horarios, fichajes y vacaciones **sí son datos
  personales**. Al guardarlos somos **encargados del tratamiento** del bar: hace falta el
  contrato del artículo 28 del RGPD, más protección y el mínimo acceso necesario. Estos datos
  **nunca** se usan para el modelo común de IA.
- **Datos de ventas para el modelo común:** son datos del negocio, sin datos personales, pero
  su uso para entrenar el modelo debe estar autorizado en el contrato (ver punto 2).

## 7. Qué queda pendiente de decidir

- El texto comercial del argumento de venta.
- El precio de cada módulo.
- La revisión legal del contrato, de la cláusula del modelo común, de la limitación de
  responsabilidad y del fichaje.
