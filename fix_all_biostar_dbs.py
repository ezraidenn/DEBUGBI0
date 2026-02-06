import sqlite3
import os

# Encontrar todas las BDs biostar_users.db
db_files = [
    'biostar_users.db',
    'instance/biostar_users.db'
]

sql_script = open('create_mobper_tables.sql', 'r').read()

for db_path in db_files:
    if os.path.exists(db_path):
        print(f'\n📊 Actualizando: {db_path}')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Eliminar tabla antigua
        cursor.execute("DROP TABLE IF EXISTS mobper_incidencias_dia")
        conn.commit()
        
        # Crear nuevas tablas
        cursor.executescript(sql_script)
        conn.commit()
        
        # Verificar
        cursor.execute("PRAGMA table_info(mobper_incidencias_dia)")
        cols = cursor.fetchall()
        print(f'  ✓ Columnas: {len(cols)}')
        for col in cols:
            if 'goce' in col[1] or 'motivo' in col[1]:
                print(f'    ✓ {col[1]} ({col[2]})')
        
        conn.close()

print('\n✅ Todas las bases de datos actualizadas')
