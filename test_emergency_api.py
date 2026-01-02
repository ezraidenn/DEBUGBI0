"""Script para probar las rutas API de emergencias."""
import sys
sys.path.insert(0, '.')

from webapp.app import app
import json

with app.test_client() as client:
    # Login como admin
    with app.app_context():
        from webapp.models import User
        admin = User.query.filter_by(username='admin').first()
        
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
    
    print("=" * 60)
    print("🧪 PROBANDO RUTAS API DE EMERGENCIAS")
    print("=" * 60)
    
    # Test 1: GET /api/zones
    print("\n1️⃣ GET /api/zones")
    response = client.get('/api/zones')
    print(f"   Status: {response.status_code}")
    data = json.loads(response.data)
    print(f"   Success: {data.get('success')}")
    print(f"   Zonas: {len(data.get('zones', []))}")
    if data.get('zones'):
        for zone in data['zones']:
            print(f"      - {zone['name']} (ID: {zone['id']})")
    
    # Test 2: GET /api/emergency/status
    print("\n2️⃣ GET /api/emergency/status")
    response = client.get('/api/emergency/status')
    print(f"   Status: {response.status_code}")
    data = json.loads(response.data)
    print(f"   Success: {data.get('success')}")
    print(f"   Has active: {data.get('has_active')}")
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas")
    print("=" * 60)
