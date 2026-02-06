import sqlite3

# Verificar biostar_users.db (la que usa la app)
conn = sqlite3.connect('biostar_users.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mobper%'")
print('📊 Tablas MobPer en biostar_users.db:')
for row in cursor.fetchall():
    print(f'  ✓ {row[0]}')
    cursor.execute(f"PRAGMA table_info({row[0]})")
    cols = cursor.fetchall()
    print(f'    Columnas: {len(cols)}')
    for col in cols:
        if 'goce' in col[1] or 'motivo' in col[1]:
            print(f'      ✓ {col[1]} ({col[2]})')

conn.close()
print('\n✅ Verificación completa')
