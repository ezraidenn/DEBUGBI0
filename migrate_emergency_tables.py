"""Script para crear las tablas de emergencias en la base de datos."""
import sys
sys.path.insert(0, '.')

from webapp.app import app
from webapp.models import db

with app.app_context():
    print("=" * 60)
    print("🔧 CREANDO TABLAS DE EMERGENCIAS")
    print("=" * 60)
    
    # Crear todas las tablas (solo crea las que no existen)
    db.create_all()
    
    print("\n✅ Tablas de emergencias creadas exitosamente")
    print("=" * 60)
    print("\nTablas disponibles:")
    print("  - zones (Zonas físicas)")
    print("  - groups (Grupos/Departamentos)")
    print("  - group_members (Miembros de grupos)")
    print("  - emergency_sessions (Sesiones de emergencia)")
    print("  - roll_call_entries (Pase de lista)")
    print("  - zone_devices (Dispositivos por zona)")
    print("=" * 60)
