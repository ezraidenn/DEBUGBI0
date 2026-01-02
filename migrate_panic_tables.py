"""Script para crear las tablas de modo pánico en la base de datos."""
import sys
sys.path.insert(0, '.')

from webapp.app import app
from webapp.models import db

with app.app_context():
    print("=" * 60)
    print("🚨 CREANDO TABLAS DE MODO PÁNICO")
    print("=" * 60)
    
    db.create_all()
    
    print("\n✅ Tablas de modo pánico creadas exitosamente")
    print("=" * 60)
    print("\nTablas disponibles:")
    print("  - panic_mode_status (Estado actual por dispositivo)")
    print("  - panic_mode_log (Log de acciones)")
    print("=" * 60)
