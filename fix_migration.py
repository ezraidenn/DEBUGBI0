"""
Script para aplicar la migración directamente a la base de datos
"""
import sqlite3
import os

DB_PATH = 'instance/biostar_users.db'

def fix_migration():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Base de datos no encontrada: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Verificar si tabla companies existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='companies'")
    if not cursor.fetchone():
        print("[FIX] Creando tabla companies...")
        cursor.execute("""
            CREATE TABLE companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                logo_filename VARCHAR(200),
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("[FIX] ✓ Tabla companies creada")
    else:
        print("[FIX] ✓ Tabla companies ya existe")
    
    # 2. Insertar empresas por defecto
    empresas = [
        ('MIT', None, 1),
        ('Ekogolf', 'Ekogolf.jpeg', 1),
        ('DRELEX', 'DRELEX.png', 1)
    ]
    
    for name, logo, active in empresas:
        cursor.execute("SELECT id FROM companies WHERE name = ?", (name,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO companies (name, logo_filename, is_active) VALUES (?, ?, ?)",
                (name, logo, active)
            )
            print(f"[FIX] ✓ Empresa creada: {name}")
        else:
            print(f"[FIX] - Empresa ya existe: {name}")
    
    # 3. Verificar columna company_id en mobper_presets
    cursor.execute("PRAGMA table_info(mobper_presets)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'company_id' in columns:
        print("[FIX] ✓ Columna company_id ya existe en mobper_presets")
    else:
        print("[FIX] ERROR: Columna company_id no existe (debería haberse agregado)")
    
    conn.commit()
    conn.close()
    
    print("\n[FIX] ✓ Migración completada exitosamente")
    print("\nVerificación final:")
    
    # Verificación final
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, logo_filename FROM companies")
    companies = cursor.fetchall()
    print(f"\nEmpresas en BD: {len(companies)}")
    for comp in companies:
        print(f"  - ID {comp[0]}: {comp[1]} (logo: {comp[2] or 'default'})")
    
    cursor.execute("PRAGMA table_info(mobper_presets)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"\nColumnas en mobper_presets: {', '.join(columns)}")
    
    conn.close()

if __name__ == '__main__':
    fix_migration()
