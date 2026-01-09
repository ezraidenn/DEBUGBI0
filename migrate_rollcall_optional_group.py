"""
Migración: Hacer group_id opcional y agregar campo manual_group_name en RollCallEntry.
Esto permite entradas manuales sin crear grupos en la BD.
"""
import sqlite3
import sys

def migrate():
    db_path = 'instance/biostar_users.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=" * 60)
        print("MIGRACIÓN: RollCallEntry - group_id opcional + manual_group_name")
        print("=" * 60)
        
        # 1. Verificar si la columna manual_group_name ya existe
        cursor.execute("PRAGMA table_info(roll_call_entries)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'manual_group_name' in columns:
            print("✓ La columna 'manual_group_name' ya existe")
        else:
            # Agregar columna manual_group_name
            print("\n1. Agregando columna 'manual_group_name'...")
            cursor.execute("""
                ALTER TABLE roll_call_entries 
                ADD COLUMN manual_group_name TEXT
            """)
            print("✓ Columna 'manual_group_name' agregada")
        
        # 2. Para hacer group_id nullable, necesitamos recrear la tabla
        # SQLite no permite modificar constraints directamente
        print("\n2. Recreando tabla para hacer group_id opcional...")
        
        # Crear tabla temporal con la nueva estructura
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roll_call_entries_new (
                id INTEGER PRIMARY KEY,
                emergency_id INTEGER NOT NULL,
                group_id INTEGER,  -- Ahora es nullable
                biostar_user_id TEXT NOT NULL,
                user_name TEXT,
                status TEXT DEFAULT 'pending',
                marked_by INTEGER,
                marked_at DATETIME,
                notes TEXT,
                manual_group_name TEXT,  -- Nuevo campo para grupos temporales
                FOREIGN KEY (emergency_id) REFERENCES emergency_sessions(id),
                FOREIGN KEY (group_id) REFERENCES groups(id),
                FOREIGN KEY (marked_by) REFERENCES users(id)
            )
        """)
        print("✓ Tabla temporal creada")
        
        # Copiar datos de la tabla original
        print("\n3. Copiando datos...")
        cursor.execute("""
            INSERT INTO roll_call_entries_new 
            (id, emergency_id, group_id, biostar_user_id, user_name, status, 
             marked_by, marked_at, notes, manual_group_name)
            SELECT id, emergency_id, group_id, biostar_user_id, user_name, status,
                   marked_by, marked_at, notes, NULL
            FROM roll_call_entries
        """)
        rows_copied = cursor.rowcount
        print(f"✓ {rows_copied} registros copiados")
        
        # Eliminar tabla original
        print("\n4. Eliminando tabla original...")
        cursor.execute("DROP TABLE roll_call_entries")
        print("✓ Tabla original eliminada")
        
        # Renombrar tabla temporal
        print("\n5. Renombrando tabla temporal...")
        cursor.execute("ALTER TABLE roll_call_entries_new RENAME TO roll_call_entries")
        print("✓ Tabla renombrada")
        
        # Commit
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print("\nCambios realizados:")
        print("  • group_id ahora es NULLABLE (opcional)")
        print("  • Agregado campo manual_group_name para grupos temporales")
        print(f"  • {rows_copied} registros migrados")
        print("\nAhora las entradas manuales NO crearán grupos en la BD.")
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ ERROR: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("\n⚠️  IMPORTANTE: Cierra el servidor Flask antes de ejecutar esta migración")
    print("Presiona Enter para continuar o Ctrl+C para cancelar...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nMigración cancelada.")
        sys.exit(0)
    
    success = migrate()
    sys.exit(0 if success else 1)
