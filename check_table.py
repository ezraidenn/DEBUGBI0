import sqlite3

conn = sqlite3.connect('instance/app.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(mobper_incidencias_dia)')
print('Columnas actuales en mobper_incidencias_dia:')
for row in cursor.fetchall():
    print(f'  {row[1]} ({row[2]})')
conn.close()
