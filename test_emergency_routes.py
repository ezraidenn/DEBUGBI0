"""Script para probar las rutas de emergencias."""
import sys
sys.path.insert(0, '.')

from webapp.app import app
from webapp.models import db, Zone, Group

with app.app_context():
    print("=" * 60)
    print("🔍 VERIFICACIÓN DE RUTAS DE EMERGENCIAS")
    print("=" * 60)
    
    # Verificar zonas
    zones = Zone.query.filter_by(is_active=True).all()
    print(f"\n📍 Zonas encontradas: {len(zones)}")
    for zone in zones:
        print(f"  - {zone.name} (ID: {zone.id})")
        
        # Verificar grupos de cada zona
        groups = Group.query.filter_by(zone_id=zone.id, is_active=True).all()
        print(f"    └─ Grupos: {len(groups)}")
        for group in groups:
            print(f"       - {group.name} (ID: {group.id}, {group.members.count()} miembros)")
    
    print("\n" + "=" * 60)
    print("✅ Verificación completa")
    print("=" * 60)
