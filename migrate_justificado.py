"""
Script de migración para agregar la columna 'justificado' a mobper_incidencias_dia
Busca en todas las bases de datos posibles
"""
import sqlite3
import os

# Buscar todas las bases de datos
db_paths = [
    'checadores.db',
    'instance/checadores.db',
    'instance/app.db',
    'webapp/checadores.db',
]

for db_path in db_paths:
    if not os.path.exists(db_path):
        print(f"No existe: {db_path}")
        continue
    
    print(f"\n=== Procesando: {db_path} ===")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Listar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"Tablas: {tables}")
        
        if 'mobper_incidencias_dia' not in tables:
            print("Tabla 'mobper_incidencias_dia' no encontrada en esta DB")
            conn.close()
            continue
        
        # Verificar columnas actuales
        cursor.execute("PRAGMA table_info(mobper_incidencias_dia)")
        columns = cursor.fetchall()
        col_names = [col[1] for col in columns]
        
        print(f"Columnas actuales: {col_names}")
        
        if 'justificado' in col_names:
            print("La columna 'justificado' ya existe")
        else:
            print("Agregando columna 'justificado'...")
            cursor.execute("ALTER TABLE mobper_incidencias_dia ADD COLUMN justificado BOOLEAN DEFAULT 1")
            conn.commit()
            print("✅ Columna 'justificado' agregada exitosamente")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

print("\n=== Migración completada ===")
