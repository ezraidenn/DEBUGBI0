import sqlite3

# Actualizar ambas bases de datos
db_files = ['biostar_users.db', 'instance/biostar_users.db']

for db_path in db_files:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(mobper_incidencias_dia)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'justificado' not in columns:
            print(f'📊 Agregando columna justificado a {db_path}...')
            cursor.execute("""
                ALTER TABLE mobper_incidencias_dia 
                ADD COLUMN justificado BOOLEAN DEFAULT 1
            """)
            conn.commit()
            print(f'  ✅ Columna agregada')
        else:
            print(f'  ℹ️ Columna justificado ya existe en {db_path}')
        
        # Verificar
        cursor.execute("PRAGMA table_info(mobper_incidencias_dia)")
        print(f'  📋 Columnas actuales:')
        for col in cursor.fetchall():
            print(f'    - {col[1]} ({col[2]})')
        
        conn.close()
    except Exception as e:
        print(f'  ❌ Error en {db_path}: {e}')

print('\n✅ Proceso completado')
