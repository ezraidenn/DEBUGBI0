"""Script para verificar grupos huérfanos."""
import sys
sys.path.insert(0, '.')

from webapp.app import app
from webapp.models import db, Zone, Group

with app.app_context():
    print("=" * 60)
    print("🔍 VERIFICACIÓN DE GRUPOS")
    print("=" * 60)
    
    # Verificar todos los grupos (incluso sin zona)
    all_groups = Group.query.all()
    print(f"\n📊 Total de grupos en BD: {len(all_groups)}")
    
    for group in all_groups:
        zone_name = group.zone.name if group.zone else "SIN ZONA"
        print(f"  - {group.name} (ID: {group.id})")
        print(f"    └─ Zona: {zone_name} (zone_id: {group.zone_id})")
        print(f"    └─ Activo: {group.is_active}")
        print(f"    └─ Miembros: {group.members.count()}")
    
    # Verificar zonas
    zones = Zone.query.all()
    print(f"\n📍 Total de zonas en BD: {len(zones)}")
    for zone in zones:
        print(f"  - {zone.name} (ID: {zone.id}, Activo: {zone.is_active})")
    
    print("\n" + "=" * 60)
