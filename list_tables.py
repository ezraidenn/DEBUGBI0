import sqlite3

conn = sqlite3.connect('instance/app.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mobper%'")
print('Tablas MobPer existentes:')
for row in cursor.fetchall():
    print(f'  - {row[0]}')
    
    # Mostrar columnas de cada tabla
    cursor.execute(f"PRAGMA table_info({row[0]})")
    print(f'    Columnas:')
    for col in cursor.fetchall():
        print(f'      {col[1]} ({col[2]})')
    print()

conn.close()
