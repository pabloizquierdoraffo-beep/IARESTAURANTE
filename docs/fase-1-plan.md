# Fase 1 – Plan del MVP (sin programar)

> **Qué es este documento:** el plan de la primera fase. Aquí no hay nada programado.
> Sirve para ponernos de acuerdo antes de gastar tiempo o dinero.
>
> **Aviso importante:** no he recibido ni el **estudio de viabilidad** ni el **prototipo navegable**.
> Todo lo que viene a continuación sale solo del texto del encargo. Cuando me los paséis,
> revisaré el plan, sobre todo en lo que toca a los capítulos 4, 6, 9 y 10 del estudio.

Fecha: 28 de septiembre de 2026

---

## Decisiones tomadas (28 de septiembre de 2026)

| Pregunta | Respuesta | Qué significa |
|---|---|---|
| ¿Dónde van los servidores? | **Empresa europea** (Scaleway u OVH) | No se contrata nada hasta que lo confirmes y veamos el precio. |
| ¿Por dónde llegan los mensajes? | **WhatsApp**, con **SMS de reserva** | Habrá que verificar la empresa en Meta antes de la fase 4. |
| ¿Hay documentación del TPV? | **No, hay que pedirla** | Correo preparado en [correo-fabricante-tpv.md](correo-fabricante-tpv.md). |
| ¿Estudio y prototipo? | **No están ahora** | Seguimos con este plan; se revisa cuando lleguen. |
| ¿Copia de 12 meses de un bar? | **Aún no hay ningún bar** | La fase 3 (previsión) queda en espera. Texto para pedirla en [texto-buscar-hosteleros.md](texto-buscar-hosteleros.md). |
| ¿Nombre comercial? | **Todavía no** | Usamos un nombre provisional. |
| ¿Existe la empresa? | **Sí** | Servirá para verificarla en Meta. |
| ¿Quién da soporte? | **Sin decidir** | De momento, número de ejemplo marcado como tal. |
| ¿Quién programa? | **Claude**, y tú revisas | Cada paso termina con una explicación de cómo comprobarlo. |
| ¿Cómo ves los avances? | **Enlace privado para el móvil** | Sin contratar servidores todavía. |
| ¿Hay hosteleros para probar? | **Ninguno aún** | Texto para pedirlo en [texto-buscar-hosteleros.md](texto-buscar-hosteleros.md). |
| ¿Solo este TPV? | **No: preparado para cualquier TPV** (BDP, Ágora, Hiopos, Soltac, Firesoft, Ticsy, Numier…) | Base común + un adaptador por TPV; primero el actual. Ver [arquitectura](arquitectura-multi-tpv-y-modulos.md) y [TPV del mercado](tpv-del-mercado.md). |
| ¿Archivos exportados a mano? | **No, solo conexión automática** | Si un TPV no tiene integración oficial, no se conecta. |
| ¿Mermas? | **Hoy no se rellenan en el TPV** | Irán en un módulo de nuestra plataforma. |
| ¿Módulos extra? | **Sí, cada uno se cobra aparte**: escandallos, mermas y compras, stock, procesos del equipo, personal según la demanda, «releve» | Después del MVP; la base queda preparada desde ya. Para cualquier empleado con permisos, en el móvil, el ordenador o la tableta. |

---

## 1. El encargo en pocas palabras

Queremos un servicio que, cada lunes, mande al dueño de un bar un mensaje de WhatsApp
que diga:

- qué días de la semana vendrá **más o menos gente**,
- qué tiene que **pedir de más o de menos** (barriles, refrescos…),
- cuánto **personal** poner y a qué horas,
- y el **porqué**, en una frase («porque hace calor y hay partido»).

Para eso:

1. Un pequeño programa (el **conector**) se instala en el ordenador del bar. Lo instala el
   técnico del TPV, no el hostelero. Cada noche lee las ventas del día y las manda cifradas
   a nuestro servidor. **Solo lee; nunca escribe en la caja.**
2. Nuestro servidor junta esas ventas con el **tiempo** (AEMET), los **festivos**, los
   **eventos** (partidos, conciertos) y lo que el propio hostelero nos cuente
   («el viernes tengo una comunión de 60»).
3. Con todo eso calcula una **previsión** para los 7 días siguientes, la compara con una
   previsión sencilla («lo mismo que el mismo día de la semana pasada») y **solo la manda
   si es mejor**.
4. Cada mes se manda otro mensaje con el **ahorro estimado en euros**, explicado.

Hay **dos entradas** a la plataforma:

- **Entrada A (nosotros):** una web para ordenador donde damos de alta bares, vemos quién
  necesita atención, el estado de los conectores y los planes.
- **Entrada B (el hostelero):** una web muy sencilla para el móvil, sin contraseña, que
  complementa al mensaje de WhatsApp.

---

## 2. Dudas abiertas (necesito respuesta antes de la fase 2 o la 4)

Las ordeno de más a menos urgente.

### Sobre el TPV (lo más importante)
1. **¿Cómo se llama el TPV?** En el encargo pone «[NOMBRE DEL TPV]».
2. **¿Qué es exactamente la «integración oficial»?** No sé si es:
   - un programa o librería del fabricante que da los datos,
   - un usuario de base de datos de **solo lectura** con unas vistas preparadas,
   - o un servicio web (API) en el propio ordenador del bar.

   Necesito la **documentación** de esa integración y acceso al **entorno de pruebas**.
   De esto depende casi todo el conector.
3. ¿El fabricante nos **permite** instalar un programa nuestro en el ordenador del bar?
   ¿Lo instalará su técnico? ¿Cobra por ello?
4. ¿Qué **versión de Windows** suelen tener los ordenadores de caja? ¿Están encendidos por
   la noche o se apagan al cerrar? (Si se apagan, el envío se hará al encenderlos.)
5. En la tabla de ventas, ¿aparecen **datos personales** (nombre del camarero, del cliente,
   NIF de una factura)? El conector los quitará antes de enviar nada, pero necesito saber
   qué columnas hay.
6. ¿Un bar con varios locales tiene **una base de datos por local** o una para todos?
7. Las tablas de **mermas y stock**: ¿las rellenan los bares de verdad o suelen estar vacías?
   Esto importa para calcular el ahorro.

### Sobre los datos para la previsión
8. ¿Cuándo tendremos la **copia de un bar con 12 meses o más** de ventas? Mejor si son
   **2 o 3 bares** distintos (uno de barrio, uno de zona turística…), porque con uno solo
   no sabremos si la previsión funciona en otros sitios.
9. ¿El bar de esa copia ha dado su **autorización por escrito** para usarla en pruebas?

### Sobre el negocio
10. **Nombre comercial** del servicio (sale en los mensajes de WhatsApp y hay que
    registrarlo en Meta).
11. ¿Qué **empresa** firma los contratos y paga los servicios? Meta pide verificar la
    empresa para usar WhatsApp Business.
12. ¿Quién es la **persona de soporte**? Su teléfono y WhatsApp saldrán en todos los
    mensajes.
13. **Cómo contamos el ahorro.** Hay que acordarlo antes de prometer nada (ver punto 8.3).
    El capítulo 9 del estudio seguramente lo trata; necesito leerlo.

---

## 3. Cómo funciona por dentro (dibujo sencillo)

```
 EN CADA BAR                          NUESTRO SERVIDOR (en la Unión Europea)
 ───────────                          ─────────────────────────────────────

 ┌──────────────┐                     ┌────────────────────────────────────┐
 │ Caja (TPV)   │                     │  1. RECEPCIÓN                      │
 │ SQL Server   │                     │     recibe las ventas de cada bar  │
 └──────┬───────┘                     │     y comprueba que son suyas      │
        │ solo lectura,               └───────────────┬────────────────────┘
        │ por la integración oficial                  │
 ┌──────▼───────┐   cada noche,       ┌───────────────▼────────────────────┐
 │  CONECTOR    │   cifrado           │  2. BASE DE DATOS                  │
 │ (lo instala  ├────────────────────►│     cada bar en su "cajón",        │
 │  el técnico) │                     │     ninguno ve el de otro          │
 │              │ si no hay internet, └───────────────┬────────────────────┘
 │ guarda lo    │ lo guarda y lo                      │
 │ pendiente    │ manda después       ┌───────────────▼────────────────────┐
 └──────────────┘                     │  3. PREVISIÓN (cada domingo noche) │
                                      │     ventas + tiempo + festivos +   │
   FUENTES DE FUERA                   │     eventos + avisos del bar       │
   ───────────────                    │     → compara con la previsión     │
   AEMET (tiempo)      ──────────────►│       sencilla; si no mejora,      │
   Festivos (BOE y                    │       no se manda como consejo     │
   boletines)          ──────────────►└───────────────┬────────────────────┘
   Ticketmaster (eventos)────────────►                │
   INE (hoteles)       ──────────────►┌───────────────▼────────────────────┐
                                      │  4. MENSAJES                       │
                                      │     lunes: previsión y consejos    │
                                      │     cada mes: ahorro en euros      │
                                      └──────┬────────────────────┬────────┘
                                             │                    │
                         ┌───────────────────▼──────┐   ┌─────────▼──────────────┐
                         │ HOSTELERO (móvil)        │   │ NOSOTROS (ordenador)   │
                         │ WhatsApp + web sencilla  │   │ Entrada A: clientes,   │
                         │ Botones: "De acuerdo",   │   │ conectores, altas,     │
                         │ "Tengo un evento",       │   │ planes, avisos         │
                         │ "Llamadme"; audio/texto  │   │                        │
                         └──────────────────────────┘   └────────────────────────┘
```

**En una frase:** el bar solo tiene que tener el ordenador de caja encendido e internet;
todo lo demás pasa en nuestro servidor, y al hostelero le llega un WhatsApp.

---

## 4. Tecnologías recomendadas y por qué

Explico cada una en una frase. Elijo cosas **conocidas, estables y con muchos
programadores disponibles**, para que el día de mañana cualquiera pueda mantenerlo.

| Pieza | Recomendación | Por qué, en sencillo |
|---|---|---|
| **Conector** (en el bar) | Programa para Windows hecho en **.NET** (la tecnología de Microsoft), que funciona como «servicio» (arranca solo con el ordenador, sin ventanas). | Es lo más natural en Windows y con SQL Server. Se instala con un instalador normal que el técnico ejecuta una vez. |
| Memoria del conector | Un archivo pequeño en el propio ordenador donde guarda lo que falta por enviar. | Si se va internet, no se pierde nada. |
| **Servidor** | **Python**. | Es el lenguaje más usado para previsiones con IA; así servidor y previsión hablan el mismo idioma y hay menos piezas. |
| **Base de datos** | **PostgreSQL**, con una regla dentro de la propia base de datos que impide que un bar vea datos de otro. | Es gratuita, muy fiable y permite esa separación «por cajones» a nivel de base de datos, no solo en la pantalla. |
| **Las dos webs** | Una sola web con dos entradas, páginas sencillas generadas en el servidor, sin efectos ni animaciones. | Carga rápido en móviles viejos y con mala cobertura, y es fácil de cumplir la regla de «letra grande, una columna». |
| **Previsión** | Empezar con modelos de referencia muy simples y luego **LightGBM** (un tipo de *gradient boosting*: muchos árboles de decisión pequeños que se corrigen unos a otros). | Es lo que pide el encargo, funciona bien con pocos datos y variables de calendario/tiempo, y permite dar **rangos** («entre 150 y 190»). |
| **WhatsApp** | La **API oficial de WhatsApp Business** de Meta, directamente o a través de un proveedor autorizado. | Es la única vía legal para mensajes automáticos. Hay que usar plantillas aprobadas por Meta. |
| SMS (alternativa) | Un proveedor europeo de SMS. | Para quien no quiera WhatsApp y para el código de acceso si WhatsApp falla. |
| **Entender audios y textos** | Pasar el audio a texto con un programa de reconocimiento de voz (puede ir en nuestro propio servidor) y usar una IA de lenguaje para sacar «qué día, qué pasa, cuánta gente». **Siempre** se le devuelve al hostelero: «He entendido: viernes, comunión, 60 personas. ¿Es correcto?». | Es la regla 7 del encargo. El audio se borra en cuanto se ha pasado a texto. |
| Acceso administrador | Correo + contraseña + código de una app de verificación en el móvil. | Doble verificación, como pide el encargo. |
| Acceso hostelero | Número de móvil + código de 6 cifras por WhatsApp (o SMS). | Sin contraseñas que olvidar. |

**Lo que NO recomiendo para empezar:** aplicaciones para instalar en el móvil,
microservicios, modelos de IA grandes para la previsión, ni gráficos en la entrada B.

---

## 5. Dónde alojarlo (decisión tuya, difícil de deshacer)

Todo tiene que estar en la **Unión Europea**. Te doy dos caminos:

| Opción | Qué es | A favor | En contra |
|---|---|---|---|
| **A. Proveedor europeo** (p. ej. Scaleway u OVHcloud, ambos franceses) | Empresa europea con centros de datos en Europa. | Menos dudas legales: los datos no dependen de una empresa de EE. UU. Más barato. | Menos servicios «ya hechos»; algo más de trabajo técnico. |
| **B. Gran nube de EE. UU. en región europea** (AWS, Google Cloud o Azure en Fráncfort, París o Madrid) | Los datos están en Europa, pero la empresa es estadounidense. | Muchísimos servicios, muy conocida. | Más cara y más compleja; hay que justificar el marco de transferencias UE-EE. UU. en el contrato RGPD. |

**Mi recomendación: A (proveedor europeo)**, porque encaja mejor con el mensaje de
«tus datos no salen de Europa» y el MVP no necesita nada especial. **No lo contrato hasta
que me digas que sí.**

---

## 6. Costes mensuales estimados

> **Son estimaciones** con precios públicos que conozco hasta mi fecha de conocimiento;
> los precios de Meta y de los proveedores cambian. Antes de contratar nada, los
> comprobaremos con la web oficial de cada uno.

### 6.1 Servidores y servicios

| Concepto | Piloto (10 locales) | ~184 locales (equilibrio) |
|---|---|---|
| Servidor(es) de la aplicación y la previsión | 20 – 50 € | 60 – 150 € |
| Base de datos gestionada con copias de seguridad | 15 – 40 € | 40 – 100 € |
| Almacenamiento de copias cifradas | < 5 € | 5 – 15 € |
| Dominio, correo, avisos de caída | 5 – 15 € | 10 – 30 € |
| IA para entender audios y textos | < 5 € | 5 – 30 € |
| **Subtotal infraestructura** | **~45 – 115 €/mes** | **~120 – 325 €/mes** |

Pago único o anual:
- **Certificado de firma de código** para el conector (evita que Windows diga «programa
  desconocido» al instalarlo): unos **200 – 500 € al año**.

### 6.2 WhatsApp (lo que pide el encargo: calcularlo antes de elegir)

Desde julio de 2025, Meta cobra **por cada mensaje de plantilla entregado**, según el
tipo de mensaje y el país. Las respuestas que mandamos cuando el hostelero nos escribe
primero (dentro de las 24 horas siguientes) son gratuitas.

Mensajes previstos por local y mes:
- 4 o 5 mensajes del lunes (previsión),
- 1 informe mensual de ahorro,
- unos pocos códigos de acceso a la web.

Según la categoría en la que Meta clasifique la plantilla (de «servicio/utilidad», más
barata, o de «marketing», más cara), cada mensaje en España cuesta **unos pocos
céntimos** (del orden de 2 a 7 céntimos). Eso da **menos de 0,50 € por local y mes**,
más la comisión del proveedor si usamos uno (suele ser de céntimos por mensaje o una
cuota fija).

| | Piloto (10 locales) | ~184 locales |
|---|---|---|
| WhatsApp (estimado) | < 10 €/mes | 50 – 150 €/mes |
| SMS de reserva (a ~7–9 céntimos cada uno, si se usa poco) | < 5 €/mes | 10 – 40 €/mes |

**Riesgo:** Meta decide la categoría de cada plantilla. Si el mensaje del lunes lo
clasifica como «marketing», cuesta más y el hostelero puede bloquearlo más fácilmente.
Hay que redactarlo como información del servicio contratado, no como publicidad.

### 6.3 Total aproximado

- **Piloto:** unos **60 – 130 € al mes**, más el certificado.
- **Con ~184 locales:** unos **200 – 500 € al mes**, es decir, **1 – 3 € por local**,
  frente a una cuota de 29 – 59 €.

No incluye: sueldos, horas de programación, soporte humano, asesoría legal ni lo que cobre
el fabricante del TPV.

---

## 7. Cuánto tiempo lleva cada fase (orientativo)

Suponiendo **un programador a tiempo completo** con mi ayuda. Depende mucho de lo rápido
que lleguen los datos y la documentación del TPV.

| Fase | Qué | Tiempo aproximado | Qué necesito de vosotros |
|---|---|---|---|
| 1 | Este plan | Hecho | Respuestas a las dudas del punto 2 |
| 2 | Las dos entradas con acceso real y datos de ejemplo **marcados como ejemplo** | 4 – 6 semanas | Nombre comercial, alojamiento elegido, 5 hosteleros para probar |
| 3 | Previsión con datos reales | 3 – 5 semanas | Copia de 12 meses (mejor 2–3 bares) |
| 4 | Conector y envío de mensajes en el entorno de pruebas del TPV | 4 – 6 semanas | Documentación y entorno de pruebas del TPV, WhatsApp Business aprobado |
| 5 | Piloto con 10 locales | 8 semanas + 2 de preparación | 10 bares que acepten, técnico del TPV para instalar |

**Total hasta terminar el piloto: unos 6 – 8 meses.** Las fases 3 y 4 se pueden solapar
en parte.

---

## 8. Cómo funcionará la previsión (explicado sin jerga)

### 8.1 Qué se predice
Para cada uno de los 7 días siguientes:
- **venta total del día**, como rango («entre 1.800 y 2.200 €»),
- **franjas horarias principales** (mañana, mediodía, tarde, noche) para el personal,
- **familias clave** (cervezas, refrescos, combinados, cocina…). Los artículos que se
  venden poco se juntan en «otros».

### 8.2 Cómo sabremos si acierta
- Se compara siempre con dos cosas:
  1. **la previsión sencilla**: «lo mismo que el mismo día de la semana pasada» (y la
     media de las últimas 4 semanas);
  2. **lo que el propio hostelero cree** que va a vender (se le pregunta con un botón al
     principio del piloto).
- Se mide el error de cada local cada semana con una medida llamada **WAPE**: en
  sencillo, «de cada 100 € que vendiste, en cuántos euros nos equivocamos».
- **Si no mejora a la previsión sencilla, no se manda como consejo.** Se manda solo la
  información («la semana pasada vendiste…») o nada.
- Con **menos de 12 meses** de datos, se avisa y los rangos son más anchos y los
  consejos más prudentes.
- Si hay un **cambio brusco** (cierre por obras, vacaciones, algo raro), se detecta y
  se avisa: «Esta semana la previsión es menos fiable porque…».

### 8.3 Cómo se calcula el ahorro (hay que acordarlo)
No voy a inventar ahorros. Propuesta inicial, que hay que validar con el capítulo 9 del
estudio y con vosotros:
- **Compras:** diferencia entre lo que el hostelero pidió y lo que se vendió, antes y
  después de usar el servicio, usando las **mermas** del TPV si están rellenas.
- **Personal:** horas de personal que el hostelero dice haber ajustado × coste por hora
  que él mismo nos indica.
- El mensaje siempre dirá **«ahorro estimado»**, pondrá **un ejemplo concreto** y
  **explicará cómo se ha calculado**. Si no hay datos suficientes, no se dará una cifra.

---

## 9. Seguridad, privacidad y legalidad

| Requisito | Cómo lo cumplimos |
|---|---|
| Un bar nunca ve los datos de otro | Cada dato lleva el «dueño» marcado y la propia base de datos bloquea el acceso cruzado. Se probará expresamente. |
| Ningún dato personal sale del bar | El conector solo envía: artículo, familia, fecha, hora, cantidad e importe, **agregados**. No envía camarero, cliente, NIF ni nada parecido. La lista de campos que salen se podrá revisar. |
| Servidores en la UE, cifrado | Alojamiento en la UE; conexión cifrada (como la de la banca online) y datos cifrados en el disco y en las copias. |
| Mínimo acceso | Cada conector tiene su propia llave y solo puede enviar datos de su bar. En la entrada A, el rol «comercial/soporte» no puede borrar datos ni cambiar precios. |
| Contrato RGPD (art. 28) | Prepararé un borrador basado en el **modelo de la AEPD** (Agencia Española de Protección de Datos). **Debe revisarlo un abogado** antes de usarlo. |
| Reglamento europeo de IA | Cada mensaje con recomendaciones lleva una línea visible: «Previsión hecha con inteligencia artificial». Las respuestas automáticas también lo dicen. (Las obligaciones de transparencia del art. 50 se aplican desde agosto de 2026.) |
| Normas de WhatsApp | Solo se escribe a quien ha dado su consentimiento al contratar; plantillas aprobadas por Meta; opción «no quiero más mensajes» siempre disponible. |
| AEMET | Se cita siempre «Fuente: AEMET» donde se use su información. |
| Nunca escribir en el TPV | El conector usa solo la integración oficial y, si es por base de datos, un usuario **de solo lectura**. |

**Nota:** los números de móvil de los hosteleros sí son datos personales (de nuestros
clientes, no de los clientes del bar). Se guardan protegidos y solo para el servicio.

---

## 10. Riesgos principales

| Riesgo | Qué puede pasar | Qué hacemos |
|---|---|---|
| **Integración del TPV desconocida** | Si no permite leer lo que necesitamos, o es lenta, el conector se complica. | Es lo primero que hay que aclarar (dudas 1–7). |
| **Pocos datos** | Con un solo bar de 12 meses no sabremos si funciona en otros. | Pedir 2–3 bares distintos; si no hay, decirlo claramente en los resultados. |
| **La previsión no mejora lo sencillo** | Pasa a menudo en bares pequeños y estables. | Se mide antes de mandar nada; si no mejora, no se envía como consejo. Así no se pierde la confianza. |
| **Ordenador del bar apagado de noche** | No llegan datos. | El conector envía al encenderse; alerta en la entrada A tras 24 h sin datos. |
| **Coste o categoría de WhatsApp** | Meta cambia precios o clasifica el mensaje como publicidad. | Redactar plantillas como información de servicio; tener SMS y correo de reserva. |
| **Festivos locales** | No hay un único sitio con los festivos de todos los municipios. | Cargar los nacionales y autonómicos del BOE y boletines; los locales se cargan a mano para los municipios de nuestros clientes (poco trabajo al principio) y el hostelero puede corregirlos. |
| **Condiciones de Ticketmaster** | Su API gratuita tiene límites de uso y condiciones. | Revisar las condiciones antes de usarla comercialmente; los eventos que mete el hostelero valen igual. |
| **Hostelero no lee los mensajes** | Riesgo de baja. | La entrada A lo detecta y avisa para llamar; seguimiento especial los primeros 90 días. |
| **Prometer ahorros no medidos** | Pérdida de confianza y problemas legales. | Siempre «estimado», con el cálculo explicado; nada de cifras sin datos. |

---

## 11. Qué necesito

### De vosotros
1. **El estudio de viabilidad** y **el prototipo navegable** (no me han llegado).
2. Respuestas a las **dudas del punto 2**.
3. **Decisión de alojamiento** (punto 5).
4. **Decisión de canal**: ¿empezamos con WhatsApp como canal principal? (necesitaremos
   verificar la empresa en Meta y un número de teléfono para el servicio).
5. La **copia de 12 meses** (mejor de 2–3 bares) con autorización del bar.
6. **5 hosteleros** ajenos al proyecto para probar la entrada B al final de la fase 2.
7. Un **abogado** que revise el contrato RGPD y el aviso de IA.

### Del fabricante del TPV
1. Documentación de la **integración oficial** y acceso al **entorno de pruebas**.
2. Confirmación de que podemos leer **solo en modo lectura** las tablas o vistas:
   SalesOrderLine, Article, ArticleTariff, TurnOverGroup, MainTurnOverGroup, mermas y stock.
3. Permiso y procedimiento para que su **técnico instale el conector**, y cómo le
   avisamos si un conector deja de funcionar.
4. Saber si hay **datos personales** en esas tablas y en qué columnas.

---

## 12. Cómo comprobar esta fase sin saber programar

- Lee este documento y comprueba que **cada punto del encargo** está recogido
  (checklist en el anexo).
- Si algo no se entiende, es culpa del documento: dímelo y lo reescribo.

## 13. Siguiente decisión que tienes que tomar

Para empezar la fase 2 necesito, como mínimo:

1. **¿Proveedor europeo (recomendado) o gran nube en región europea?**
2. **¿Empezamos con WhatsApp** (con SMS de reserva) como canal principal?
3. **Mandarme el estudio y el prototipo**, y el **nombre del TPV** con su documentación.

---

## Anexo – Checklist del encargo

| Punto del encargo | Dónde se trata |
|---|---|
| Entrada A: resumen, «qué hacer hoy», clientes, altas, conectores, planes, acceso seguro y roles | §1, §4, §9 (se construye en la fase 2) |
| Entrada B: acceso por móvil, semana, avisar, ahorro, ayuda, cambio de local | §1, §4 (fase 2) |
| Reglas de facilidad de uso 1–10 | §3, §4 (fase 2, probado con 5 hosteleros) |
| Conector local, cifrado, pendiente sin internet, aviso | §3, §4, §10 (fase 4) |
| Previsión 7 días, franjas, familias, agrupar lo poco vendido | §8.1 (fase 3) |
| AEMET, festivos, Ticketmaster, INE; no Open-Meteo gratuito | §3, §10 |
| Mensaje del lunes y correcciones por botón, texto o audio | §3, §4 |
| Informe mensual de ahorro | §8.3 |
| 12 meses, comparación con referencia y con el hostelero, WAPE, rangos, motivos, cambios bruscos | §8.2 |
| Separación de clientes, sin datos personales, UE, cifrado, RGPD art. 28, IA, WhatsApp | §9 |
| Costes, riesgos, lo que necesitamos | §6, §10, §11 |
| Fuera del MVP (pedidos automáticos, turnos completos, chat abierto, cobro automático) | No se incluye nada de esto |
| Otros TPV | La base común entra en el MVP; en el piloto solo se conecta el TPV actual |
| Módulos de pago (escandallos, mermas y compras, stock, equipo, personal) | Después del MVP; tablas de módulos y permisos preparadas desde la fase 2 |
