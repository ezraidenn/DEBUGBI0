-- Migración para agregar tabla de incidencias individuales
-- Ejecutar después de crear las tablas base de MobPer

CREATE TABLE IF NOT EXISTS mobper_incidencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    fecha DATE NOT NULL,
    estado_auto VARCHAR(20),
    clasificacion VARCHAR(50),
    observaciones TEXT,
    hora_entrada TIME,
    minutos_diferencia INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES mobper_users(id),
    UNIQUE(user_id, fecha)
);

CREATE INDEX IF NOT EXISTS idx_incidencias_user_fecha ON mobper_incidencias(user_id, fecha);
CREATE INDEX IF NOT EXISTS idx_incidencias_clasificacion ON mobper_incidencias(clasificacion);
