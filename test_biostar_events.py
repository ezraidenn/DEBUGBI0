"""
Script para verificar si BioStar tiene eventos reales
"""
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import requests
from requests.auth import HTTPBasicAuth

# Cargar variables de entorno
load_dotenv()

BIOSTAR_HOST = os.getenv('BIOSTAR_HOST', 'https://10.0.0.100')
BIOSTAR_USER = os.getenv('BIOSTAR_USER', 'admin')
BIOSTAR_PASSWORD = os.getenv('BIOSTAR_PASSWORD', 'admin')

print(f"🔍 Verificando eventos en BioStar")
print(f"Host: {BIOSTAR_HOST}")
print(f"Usuario: {BIOSTAR_USER}")
print("=" * 60)

# Autenticar
try:
    auth_url = f"{BIOSTAR_HOST}/api/login"
    print(f"\n1. Autenticando en: {auth_url}")
    
    response = requests.post(
        auth_url,
        json={'User': {'login_id': BIOSTAR_USER, 'password': BIOSTAR_PASSWORD}},
        verify=False,
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ Error de autenticación: {response.status_code}")
        print(f"Response: {response.text}")
        exit(1)
    
    print(f"✅ Respuesta: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    # El session_id viene en el header, no en el body
    session_id = response.headers.get('bs-session-id')
    if not session_id:
        print(f"❌ No se encontró session_id en headers")
        print(f"Response body: {response.text}")
        exit(1)
    
    print(f"✅ Autenticado. Session ID: {session_id[:20]}...")
    
    # Obtener eventos usando el endpoint de búsqueda
    today = datetime.now().strftime('%Y-%m-%dT00:00:00.000Z')
    now = datetime.now().strftime('%Y-%m-%dT23:59:59.999Z')
    
    events_url = f"{BIOSTAR_HOST}/api/events/search"
    headers = {
        'bs-session-id': session_id,
        'Content-Type': 'application/json'
    }
    
    print(f"\n2. Consultando eventos del día de hoy (usando search)")
    print(f"URL: {events_url}")
    print(f"Rango: {today} a {now}")
    
    payload = {
        "Query": {
            "limit": 100,
            "offset": 0
        },
        "EventFilter": {
            "start_datetime": today,
            "end_datetime": now
        }
    }
    
    response = requests.post(
        events_url,
        headers=headers,
        json=payload,
        verify=False,
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ Error obteniendo eventos: {response.status_code}")
        print(f"Response: {response.text}")
        exit(1)
    
    data = response.json()
    events = data.get('EventCollection', {}).get('rows', [])
    total = data.get('EventCollection', {}).get('total', 0)
    
    print(f"\n✅ Eventos encontrados: {total}")
    print(f"📊 Eventos en esta página: {len(events)}")
    
    if len(events) > 0:
        print("\n📋 Primeros 5 eventos:")
        for i, event in enumerate(events[:5], 1):
            user_info = event.get('user_id', {})
            user_name = user_info.get('name', 'Desconocido') if isinstance(user_info, dict) else 'N/A'
            event_time = event.get('datetime', 'N/A')
            device_id = event.get('device_id', {}).get('id', 'N/A')
            event_type = event.get('event_type_id', {}).get('code', 'N/A')
            
            print(f"\n  Evento {i}:")
            print(f"    Usuario: {user_name}")
            print(f"    Hora: {event_time}")
            print(f"    Dispositivo: {device_id}")
            print(f"    Tipo: {event_type}")
    else:
        print("\n⚠️  No hay eventos registrados hoy")
        print("Esto explica por qué los contadores están en cero")
    
    # Logout
    logout_url = f"{BIOSTAR_HOST}/api/logout"
    requests.post(logout_url, headers=headers, verify=False, timeout=5)
    print("\n✅ Sesión cerrada")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
