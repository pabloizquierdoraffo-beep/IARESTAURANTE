# Servidor de la plataforma

La web y la base de datos centrales. Tiene tres entradas:

| Entrada | Para quién | Cómo se entra |
|---|---|---|
| `/entrar` → Semana, Avisar, Ahorro, Módulos, Ayuda | Dueño o encargado del bar (móvil) | Su móvil + código de 6 números |
| `/entrar` → Inicio | Empleados | Su móvil + código |
| `/admin` | Nosotros (administrador y comercial/soporte) | Correo + contraseña + código de la app de verificación |
| `/api/conector/v1/paquetes` | El conector del bar | Token del conector |

## Lo que ya funciona

- **Separación de clientes en la propia base de datos.** Cada fila lleva su cliente y PostgreSQL
  solo deja ver las del cliente de la conexión. La aplicación entra con un usuario que no puede
  saltarse esa regla. Aunque alguien cambiara la dirección de la página a mano, no vería nada ajeno.
- **Acceso del bar sin contraseña:** móvil y código de 6 números. Dura 10 minutos, admite como
  mucho 5 intentos y se pueden pedir como mucho 3 códigos cada 15 minutos. A quien no es cliente
  se le contesta igual, para no desvelar qué números son clientes.
- **Acceso de la plataforma con doble verificación** y dos roles: el comercial/soporte no puede
  cambiar planes, módulos ni conectores.
- **Alta de un bar** con su prueba gratis de 2 meses. No deja darlo de alta sin el contrato RGPD.
- **Resumen** con ingresos, locales conectados, avance hacia los 184 locales y «qué hay que hacer
  hoy»: conectores sin datos más de 24 h, clientes que no leen y pruebas que acaban.
- **Ficha del cliente:**
  - mensaje de prueba;
  - aviso al técnico (queda registrado);
  - cambio de plan;
  - módulos contratados;
  - crear el conector: el token se enseña una sola vez y no se guarda.
- **Avisar** en dos toques o con sus palabras («el viernes tengo una comunión de 60»). Siempre se
  pide confirmar lo entendido antes de guardarlo.
- **Recepción de datos del conector:** solo acepta el idioma común; cualquier otro campo se
  rechaza entero. Reenviar el mismo día no duplica las ventas.
- **Tablas preparadas para los módulos de pago** (contratados y permisos por empleado).

## Lo que todavía no hace

- **Previsión real** (fase 3): hasta tener 12 meses de ventas solo hay una previsión de ejemplo, marcada.
- **WhatsApp y SMS** (fase 4): de momento el código de acceso se enseña en pantalla, y solo en la
  versión de pruebas (`MODO_DESARROLLO=1`).
- **Informe de ahorro:** no se muestra ninguna cifra hasta poder medirla.
- **Los módulos de pago** en sí: se construyen después del MVP.
- **Puesta en internet:** falta contratar el servidor europeo (se pedirá permiso antes).

## Pruebas automáticas (37)

```bash
pip install -r requirements-pruebas.txt
PRUEBAS_PG_ADMIN_URL="postgresql://postgres:...@localhost/postgres" python -m pytest
```

Crean una base de datos nueva, la prueban y la borran. Sin `PRUEBAS_PG_ADMIN_URL`, se saltan.

## Arrancarlo en un ordenador de pruebas

```bash
pip install -r requirements.txt
# 1. Tablas y usuario de la aplicación (con el usuario dueño de la base de datos)
python -m app.preparar_bd "postgresql://dueño:...@localhost/basedatos" app_web "<contraseña app>"
export DATABASE_URL="postgresql://app_web:<contraseña app>@localhost/basedatos"
# 2. Datos de ejemplo (opcional) y un usuario administrador
python -m app.datos_ejemplo
python -m app.crear_usuario tu@correo.es admin
# 3. Arrancar
CLAVE_SECRETA="<al menos 32 caracteres>" MODO_DESARROLLO=1 COOKIES_SEGURAS=0 \
  uvicorn app.main:crear_app --factory --port 8000
```

Con los datos de ejemplo se puede entrar como dueño con el móvil **600 000 001** y como empleada
con el **600 000 011**. El código aparece en pantalla porque es la versión de pruebas.

En producción: `MODO_DESARROLLO=0`, `COOKIES_SEGURAS=1`, https obligatorio y servidor en la UE.
