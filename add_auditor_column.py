import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('instance/biostar_users.db')
cursor = conn.cursor()

# Verificar columnas actuales
cursor.execute('PRAGMA table_info(users)')
columns = cursor.fetchall()

print('Columnas en tabla users:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')

# Verificar si existe is_auditor
has_auditor = any('is_auditor' in str(col) for col in columns)
print(f'\n¿Tiene columna is_auditor? {has_auditor}')

if not has_auditor:
    print('\nAgregando columna is_auditor...')
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN is_auditor BOOLEAN DEFAULT 0')
        conn.commit()
        print('✅ Columna is_auditor agregada exitosamente')
    except Exception as e:
        print(f'❌ Error: {e}')
else:
    print('\n✅ La columna is_auditor ya existe')

# Activar is_auditor para el usuario auditor@gmail.com
print('\nActivando is_auditor para auditor@gmail.com...')
cursor.execute("UPDATE users SET is_auditor = 1 WHERE email = 'auditor@gmail.com'")
conn.commit()

# Verificar
cursor.execute("SELECT username, email, is_admin, is_auditor FROM users WHERE email = 'auditor@gmail.com'")
user = cursor.fetchone()
if user:
    print(f'Usuario: {user[0]}')
    print(f'Email: {user[1]}')
    print(f'is_admin: {user[2]}')
    print(f'is_auditor: {user[3]}')
    print('✅ Usuario actualizado correctamente')
else:
    print('❌ Usuario no encontrado')

conn.close()
