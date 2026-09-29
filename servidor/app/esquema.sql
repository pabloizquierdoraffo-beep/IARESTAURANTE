-- Esquema de la plataforma.
--
-- Regla principal: un cliente (bar o grupo) nunca puede ver los datos de otro.
-- Se impone en la propia base de datos con "seguridad por filas" (RLS): cada tabla con datos
-- de un cliente lleva cliente_id y una política que solo deja ver las filas del cliente
-- fijado en la conexión (app.cliente_id). Solo las pantallas de la plataforma (nosotros)
-- fijan app.es_plataforma = 'si' para ver a todos.
--
-- La aplicación se conecta con un usuario que NO es el dueño de las tablas, así que las
-- políticas se le aplican siempre. Las funciones SECURITY DEFINER de abajo son las únicas
-- que buscan fuera del cliente (para el acceso por móvil y por token del conector).

CREATE OR REPLACE FUNCTION app_cliente() RETURNS uuid
LANGUAGE sql STABLE AS $$ SELECT NULLIF(current_setting('app.cliente_id', true), '')::uuid $$;

CREATE OR REPLACE FUNCTION app_es_plataforma() RETURNS boolean
LANGUAGE sql STABLE AS $$ SELECT coalesce(current_setting('app.es_plataforma', true), '') = 'si' $$;

-- ---------- Catálogos (iguales para todos) ----------

CREATE TABLE planes (
    codigo      text PRIMARY KEY,
    nombre      text NOT NULL,
    precio_eur  numeric(8,2) NOT NULL          -- por local y mes
);

CREATE TABLE modulos (
    codigo      text PRIMARY KEY,
    nombre      text NOT NULL,
    descripcion text NOT NULL,
    incluido    boolean NOT NULL DEFAULT false, -- true = viene con todos los planes
    orden       int NOT NULL
);

INSERT INTO planes (codigo, nombre, precio_eur) VALUES
    ('basico', 'Básico', 29), ('estandar', 'Estándar', 39), ('grupo', 'Grupo', 59);

-- Los módulos de pago aún no tienen precio: se decidirá más adelante.
INSERT INTO modulos (codigo, nombre, descripcion, incluido, orden) VALUES
    ('prevision',   'Previsión y mensaje del lunes', 'Previsión de 7 días, consejos, avisos e informe de ahorro.', true, 0),
    ('turnos',      'Turnos según la previsión', 'Cuántas personas poner y a qué horas, según la previsión y las reservas.', false, 1),
    ('preparacion', 'Preparación y descongelación', 'Qué sacar y descongelar cada día según lo que se espera vender.', false, 2),
    ('escandallos', 'Escandallos, relevé y mermas', 'Coste de cada plato, relevé diario con lo perdido y control de mermas y compras.', false, 3),
    ('empleados',   'Empleados: fichaje, turnos y vacaciones', 'Cada empleado ficha y ve sus turnos y vacaciones.', false, 4);

-- ---------- Nosotros (la plataforma) ----------

CREATE TABLE usuarios_plataforma (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email           text NOT NULL UNIQUE,
    hash_contrasena text NOT NULL,
    totp_secreto    text NOT NULL,
    rol             text NOT NULL CHECK (rol IN ('admin', 'comercial')),
    activo          boolean NOT NULL DEFAULT true,
    creado_en       timestamptz NOT NULL DEFAULT now()
);

-- ---------- Datos de cada cliente ----------

CREATE TABLE clientes (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre          text NOT NULL,
    municipio       text NOT NULL,
    contacto_nombre text NOT NULL,
    contacto_movil  text NOT NULL,
    plan            text NOT NULL REFERENCES planes(codigo),
    estado          text NOT NULL CHECK (estado IN ('prueba', 'activo', 'baja')),
    prueba_hasta    date,
    rgpd_firmado_en timestamptz NOT NULL,
    es_ejemplo      boolean NOT NULL DEFAULT false,
    creado_en       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE locales (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id  uuid NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    nombre      text NOT NULL,
    municipio   text NOT NULL,
    tpv         text NOT NULL,
    id_en_tpv   text,                -- cómo llama el TPV a este local (DSTNet: "Empresa-Establecimiento")
    es_ejemplo  boolean NOT NULL DEFAULT false,
    UNIQUE (cliente_id, id_en_tpv)
);

-- Dueños y empleados de los bares. Entran con su móvil.
CREATE TABLE personas (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id  uuid NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    nombre      text NOT NULL,
    movil       text NOT NULL UNIQUE,
    rol         text NOT NULL CHECK (rol IN ('dueno', 'empleado')),
    activo      boolean NOT NULL DEFAULT true,
    es_ejemplo  boolean NOT NULL DEFAULT false
);

CREATE TABLE modulos_contratados (
    cliente_id  uuid NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    modulo      text NOT NULL REFERENCES modulos(codigo),
    desde       date NOT NULL DEFAULT current_date,
    PRIMARY KEY (cliente_id, modulo)
);

-- Qué módulos puede usar cada empleado (el dueño los ve todos los contratados).
CREATE TABLE permisos (
    cliente_id  uuid NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    persona_id  uuid NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    modulo      text NOT NULL REFERENCES modulos(codigo),
    PRIMARY KEY (persona_id, modulo)
);

CREATE TABLE conectores (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id   uuid NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    tpv          text NOT NULL,
    hash_token   text NOT NULL UNIQUE,   -- solo guardamos el resumen, nunca el token
    ultimo_envio timestamptz,
    creado_en    timestamptz NOT NULL DEFAULT now()
);

-- Datos que llegan del conector, en el idioma común. Agrupados y sin datos personales.
CREATE TABLE ventas_hora (
    cliente_id      uuid NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    local_id        uuid NOT NULL REFERENCES locales(id) ON DELETE CASCADE,
    fecha           date NOT NULL,
    hora            smallint NOT NULL CHECK (hora BETWEEN 0 AND 23),
    articulo_id     text NOT NULL,
    articulo_nombre text NOT NULL,
    familia_id      text,
    unidades        numeric(12,3) NOT NULL,
    importe         numeric(12,2) NOT NULL,
    PRIMARY KEY (local_id, fecha, hora, articulo_id, articulo_nombre)
);

CREATE TABLE tickets_hora (
    cliente_id  uuid NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    local_id    uuid NOT NULL REFERENCES locales(id) ON DELETE CASCADE,
    fecha       date NOT NULL,
    hora        smallint NOT NULL CHECK (hora BETWEEN 0 AND 23),
    tickets     int NOT NULL,
    comensales  int NOT NULL,
    PRIMARY KEY (local_id, fecha, hora)
);

CREATE TABLE familias (
    cliente_id       uuid NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    id               text NOT NULL,
    nombre           text NOT NULL,
    principal_id     text,
    principal_nombre text,
    PRIMARY KEY (cliente_id, id)
);

CREATE TABLE articulos (
    cliente_id  uuid NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    id          text NOT NULL,
    nombre      text NOT NULL,
    familia_id  text,
    se_vende    boolean NOT NULL,
    PRIMARY KEY (cliente_id, id)
);

CREATE TABLE precios (
    cliente_id  uuid NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    articulo_id text NOT NULL,
    tarifa_id   text NOT NULL,
    precio      numeric(10,2) NOT NULL,
    PRIMARY KEY (cliente_id, articulo_id, tarifa_id)
);

-- Previsión de la semana: los 3 consejos y el día a día. Hasta la fase 3 solo hay de ejemplo.
CREATE TABLE previsiones_semana (
    cliente_id     uuid NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    local_id       uuid NOT NULL REFERENCES locales(id) ON DELETE CASCADE,
    semana_inicio  date NOT NULL,          -- lunes
    consejos       jsonb NOT NULL,         -- [{etiqueta, texto, porque}]
    dias           jsonb NOT NULL,         -- [{fecha, tiempo, nivel, clientes_min, clientes_max, franjas}]
    es_ejemplo     boolean NOT NULL DEFAULT false,
    PRIMARY KEY (local_id, semana_inicio)
);

-- Lo que nos cuenta el hostelero (evento, reserva grande, cierre…). Se guarda para aprender.
CREATE TABLE avisos (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id  uuid NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    local_id    uuid NOT NULL REFERENCES locales(id) ON DELETE CASCADE,
    persona_id  uuid REFERENCES personas(id) ON DELETE SET NULL,
    fecha       date NOT NULL,
    motivo      text NOT NULL,
    personas    int,
    texto_libre text,
    creado_en   timestamptz NOT NULL DEFAULT now()
);

-- Mensajes enviados (para saber quién los lee).
CREATE TABLE mensajes (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id  uuid NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    tipo        text NOT NULL,
    enviado_en  timestamptz NOT NULL DEFAULT now(),
    leido_en    timestamptz
);

-- Registro de lo que hacemos nosotros y de lo que piden los clientes.
CREATE TABLE registro_acciones (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id  uuid NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    quien       text NOT NULL,
    accion      text NOT NULL,
    detalle     text,
    creado_en   timestamptz NOT NULL DEFAULT now()
);

-- Códigos de acceso por móvil (se guarda solo su resumen).
CREATE TABLE codigos_acceso (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    persona_id  uuid NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    hash_codigo text NOT NULL,
    caduca_en   timestamptz NOT NULL,
    intentos    int NOT NULL DEFAULT 0,
    usado       boolean NOT NULL DEFAULT false,
    creado_en   timestamptz NOT NULL DEFAULT now()
);

-- ---------- Seguridad por filas ----------

DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['locales', 'personas', 'modulos_contratados', 'permisos', 'conectores',
                             'ventas_hora', 'tickets_hora', 'familias', 'articulos', 'precios',
                             'previsiones_semana', 'avisos', 'mensajes', 'registro_acciones']
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format(
            'CREATE POLICY solo_su_cliente ON %I USING (app_es_plataforma() OR cliente_id = app_cliente()) '
            'WITH CHECK (app_es_plataforma() OR cliente_id = app_cliente())', t);
    END LOOP;
END $$;

ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;
CREATE POLICY solo_su_cliente ON clientes
    USING (app_es_plataforma() OR id = app_cliente())
    WITH CHECK (app_es_plataforma() OR id = app_cliente());

-- Los códigos de acceso no tienen cliente_id: la aplicación solo los usa ya sabiendo la persona.

-- ---------- Búsquedas antes de saber el cliente ----------

-- Para entrar por móvil: devuelve la persona y su cliente, solo si está activa.
CREATE OR REPLACE FUNCTION buscar_persona_por_movil(p_movil text)
RETURNS TABLE (persona_id uuid, cliente_id uuid)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT p.id, p.cliente_id FROM personas p
    JOIN clientes c ON c.id = p.cliente_id
    WHERE p.movil = p_movil AND p.activo AND c.estado <> 'baja'
$$;

-- Para el conector: devuelve el conector y su cliente a partir del resumen del token.
CREATE OR REPLACE FUNCTION buscar_conector_por_token(p_hash text)
RETURNS TABLE (conector_id uuid, cliente_id uuid, tpv text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT id, cliente_id, tpv FROM conectores WHERE hash_token = p_hash
$$;
