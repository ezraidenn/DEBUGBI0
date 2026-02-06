-- Crear tablas de MobPer manualmente

CREATE TABLE IF NOT EXISTS mobper_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_socio VARCHAR(20) UNIQUE NOT NULL,
    nombre_completo VARCHAR(200) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mobper_presets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    nombre_formato VARCHAR(200),
    departamento_formato VARCHAR(100),
    jefe_directo_nombre VARCHAR(200),
    hora_entrada_default TIME NOT NULL,
    tolerancia_segundos INTEGER DEFAULT 600,
    dias_descanso TEXT DEFAULT '[5, 6]',
    lista_inhabiles TEXT DEFAULT '[]',
    vigente_desde DATE NOT NULL,
    vigente_hasta DATE,
    FOREIGN KEY (user_id) REFERENCES mobper_users(id)
);

CREATE TABLE IF NOT EXISTS mobper_incidencias_dia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    fecha DATE NOT NULL,
    estado_auto VARCHAR(20),
    clasificacion VARCHAR(50),
    con_goce_sueldo BOOLEAN DEFAULT 1,
    motivo_auto VARCHAR(200),
    hora_entrada TIME,
    minutos_diferencia INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES mobper_users(id),
    UNIQUE(user_id, fecha)
);

CREATE TABLE IF NOT EXISTS mobper_periodos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    periodo_inicio DATE NOT NULL,
    periodo_fin DATE NOT NULL,
    preset_snapshot TEXT,
    raw_daily_first_checkins TEXT,
    raw_daily_status_auto TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pdf_generated_at TIMESTAMP,
    pdf_hash VARCHAR(64),
    FOREIGN KEY (user_id) REFERENCES mobper_users(id)
);
