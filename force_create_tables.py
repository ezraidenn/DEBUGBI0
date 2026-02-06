from webapp.app import app, db
from webapp.models import MobPerUser, PresetUsuario, IncidenciaDia

with app.app_context():
    # Crear todas las tablas
    db.create_all()
    
    # Verificar que se crearon
    import sqlite3
    conn = sqlite3.connect('instance/app.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mobper%'")
    print('Tablas MobPer creadas:')
    for row in cursor.fetchall():
        print(f'  ✓ {row[0]}')
        
        # Mostrar columnas
        cursor.execute(f"PRAGMA table_info({row[0]})")
        for col in cursor.fetchall():
            print(f'      - {col[1]} ({col[2]})')
        print()
    
    conn.close()
    print('✅ Proceso completado')
