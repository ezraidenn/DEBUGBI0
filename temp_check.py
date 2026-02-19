import sqlite3
conn = sqlite3.connect('instance/biostar_users.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(tables)
conn.close()
