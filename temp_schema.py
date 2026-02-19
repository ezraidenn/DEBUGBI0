import sqlite3
conn = sqlite3.connect('instance/biostar_users.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(mobper_incidencias)")
info = cursor.fetchall()
print(info)
conn.close()
