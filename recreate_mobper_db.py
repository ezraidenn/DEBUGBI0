import sqlite3

conn = sqlite3.connect('instance/app.db')
cursor = conn.cursor()

# Leer y ejecutar el SQL
with open('create_mobper_tables.sql', 'r') as f:
    sql_script = f.read()
    cursor.executescript(sql_script)

conn.commit()

# Verificar que se crearon
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mobper%'")
print('✅ Tablas MobPer creadas:')
for row in cursor.fetchall():
    print(f'  - {row[0]}')
    cursor.execute(f"PRAGMA table_info({row[0]})")
    for col in cursor.fetchall():
        print(f'      {col[1]} ({col[2]})')
    print()

conn.close()
print('✅ Base de datos lista')
