import sqlite3

conn = sqlite3.connect('biostar_users.db')
cursor = conn.cursor()

# Eliminar tabla antigua si existe
cursor.execute("DROP TABLE IF EXISTS mobper_incidencias_dia")
conn.commit()

# Leer y ejecutar el SQL completo
with open('create_mobper_tables.sql', 'r') as f:
    sql_script = f.read()
    cursor.executescript(sql_script)

conn.commit()

# Verificar
cursor.execute("PRAGMA table_info(mobper_incidencias_dia)")
print('✅ Columnas en mobper_incidencias_dia:')
for col in cursor.fetchall():
    print(f'  - {col[1]} ({col[2]})')

conn.close()
print('\n✅ Base de datos biostar_users.db actualizada')
