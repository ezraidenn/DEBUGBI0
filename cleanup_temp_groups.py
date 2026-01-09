"""
Script para eliminar grupos temporales creados por el código anterior.
Estos grupos tienen la descripción "Grupo temporal para entradas manuales".
"""
import sqlite3

def cleanup():
    db_path = 'instance/biostar_users.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=" * 60)
        print("LIMPIEZA: Eliminar grupos temporales antiguos")
        print("=" * 60)
        
        # Buscar grupos temporales
        cursor.execute("""
            SELECT id, name, description, zone_id
            FROM groups
            WHERE description LIKE '%Grupo temporal para entradas manuales%'
            AND is_active = 1
        """)
        
        temp_groups = cursor.fetchall()
        
        if not temp_groups:
            print("\n✓ No hay grupos temporales antiguos para eliminar")
            return True
        
        print(f"\n📋 Encontrados {len(temp_groups)} grupos temporales antiguos:")
        for group in temp_groups:
            print(f"  • ID {group[0]}: {group[1]} (Zona {group[3]})")
        
        print("\n⚠️  Estos grupos fueron creados por el código anterior.")
        print("¿Deseas eliminarlos? (s/n): ", end="")
        response = input().strip().lower()
        
        if response != 's':
            print("\nLimpieza cancelada.")
            return False
        
        # Actualizar entradas de roll_call que usan estos grupos
        # Mover el nombre del grupo a manual_group_name
        print("\n1. Actualizando entradas de pase de lista...")
        for group_id, group_name, _, _ in temp_groups:
            cursor.execute("""
                UPDATE roll_call_entries
                SET manual_group_name = ?,
                    group_id = NULL
                WHERE group_id = ?
            """, (group_name, group_id))
            updated = cursor.rowcount
            if updated > 0:
                print(f"  ✓ {updated} entradas actualizadas para grupo '{group_name}'")
        
        # Marcar grupos como inactivos (soft delete)
        print("\n2. Eliminando grupos temporales...")
        for group_id, group_name, _, _ in temp_groups:
            cursor.execute("""
                UPDATE groups
                SET is_active = 0
                WHERE id = ?
            """, (group_id,))
            print(f"  ✓ Grupo '{group_name}' eliminado")
        
        # Commit
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✅ LIMPIEZA COMPLETADA")
        print("=" * 60)
        print(f"\n• {len(temp_groups)} grupos temporales eliminados")
        print("• Entradas de pase de lista actualizadas")
        print("• Ahora los grupos son 100% temporales (solo texto)")
        
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
    print("\n⚠️  Este script eliminará grupos temporales creados por el código anterior")
    print("Presiona Enter para continuar o Ctrl+C para cancelar...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nLimpieza cancelada.")
        exit(0)
    
    success = cleanup()
    exit(0 if success else 1)
