import sqlite3

conn = sqlite3.connect('checadores.db')
c = conn.cursor()

# List all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:', [t[0] for t in c.fetchall()])

# Check if mobper_incidencias_dia exists and its columns
try:
    c.execute("PRAGMA table_info(mobper_incidencias_dia)")
    cols = c.fetchall()
    print('Columns in mobper_incidencias_dia:', [col[1] for col in cols])
    
    # Check if justificado column exists
    col_names = [col[1] for col in cols]
    if 'justificado' not in col_names and cols:
        print('Adding justificado column...')
        c.execute("ALTER TABLE mobper_incidencias_dia ADD COLUMN justificado BOOLEAN DEFAULT 1")
        conn.commit()
        print('Column added!')
    elif 'justificado' in col_names:
        print('justificado column already exists')
    else:
        print('Table may not exist yet')
except Exception as e:
    print(f'Error: {e}')

conn.close()
