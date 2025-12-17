"""
Script para investigar API de usuarios en BioStar 2
"""
import sys
import os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

import requests
import urllib3
urllib3.disable_warnings()

# Credenciales
host = os.getenv('BIOSTAR_HOST', 'https://10.0.0.100')
user = os.getenv('BIOSTAR_USER', 'admin')
password = os.getenv('BIOSTAR_PASSWORD', '')

session = requests.Session()

# Login
print('=== Login ===')
login_resp = session.post(
    f"{host}/api/login",
    json={"User": {"login_id": user, "password": password}},
    verify=False,
    timeout=30
)
if login_resp.status_code != 200:
    print(f"Error login: {login_resp.status_code}")
    exit(1)

token = login_resp.headers.get('bs-session-id')
print(f"Token: {token[:20]}...")

headers = {"bs-session-id": token, "Content-Type": "application/json"}

# 1. GET /api/users - Obtener todos los usuarios
print('\n=== 1. GET /api/users ===')
try:
    resp = session.get(f"{host}/api/users", headers=headers, verify=False, timeout=30)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        users = data.get('UserCollection', {}).get('rows', [])
        print(f"Usuarios encontrados: {len(users)}")
        for u in users[:5]:
            print(f"  ID: {u.get('user_id')} - {u.get('name')}")
        if len(users) > 5:
            print(f"  ... y {len(users) - 5} más")
    else:
        print(f"Response: {resp.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

# 2. POST /api/users/search - Buscar usuarios
print('\n=== 2. POST /api/users/search ===')
try:
    payload = {
        "Query": {
            "limit": 50,
            "conditions": []
        }
    }
    resp = session.post(f"{host}/api/users/search", json=payload, headers=headers, verify=False, timeout=30)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        users = data.get('UserCollection', {}).get('rows', [])
        print(f"Usuarios encontrados: {len(users)}")
        for u in users[:5]:
            print(f"  ID: {u.get('user_id')} - {u.get('name')}")
    else:
        print(f"Response: {resp.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

# 3. POST /api/users/search con filtro de nombre
print('\n=== 3. POST /api/users/search con filtro "raul" ===')
try:
    payload = {
        "Query": {
            "limit": 50,
            "conditions": [
                {
                    "column": "name",
                    "operator": 4,  # LIKE/contains
                    "values": ["raul"]
                }
            ]
        }
    }
    resp = session.post(f"{host}/api/users/search", json=payload, headers=headers, verify=False, timeout=30)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        users = data.get('UserCollection', {}).get('rows', [])
        print(f"Usuarios encontrados: {len(users)}")
        for u in users[:10]:
            print(f"  ID: {u.get('user_id')} - {u.get('name')}")
    else:
        print(f"Response: {resp.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# 4. GET /api/users con query parameter
print('\n=== 4. GET /api/users?name=raul ===')
try:
    resp = session.get(f"{host}/api/users?name=raul", headers=headers, verify=False, timeout=30)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        users = data.get('UserCollection', {}).get('rows', [])
        print(f"Usuarios encontrados: {len(users)}")
        for u in users[:10]:
            print(f"  ID: {u.get('user_id')} - {u.get('name')}")
    else:
        print(f"Response: {resp.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

# 5. GET /api/users con limit y offset
print('\n=== 5. GET /api/users?limit=100&offset=0 ===')
try:
    resp = session.get(f"{host}/api/users?limit=100&offset=0", headers=headers, verify=False, timeout=30)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        users = data.get('UserCollection', {}).get('rows', [])
        total = data.get('UserCollection', {}).get('total', 0)
        print(f"Usuarios: {len(users)} de {total} total")
        for u in users[:5]:
            print(f"  ID: {u.get('user_id')} - {u.get('name')}")
    else:
        print(f"Response: {resp.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

# 6. Ver estructura de un usuario
print('\n=== 6. Estructura de usuario ===')
try:
    resp = session.get(f"{host}/api/users?limit=1", headers=headers, verify=False, timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        users = data.get('UserCollection', {}).get('rows', [])
        if users:
            user = users[0]
            print("Campos disponibles:")
            for key in user.keys():
                val = user.get(key)
                if isinstance(val, dict):
                    print(f"  {key}: {val}")
                elif isinstance(val, list):
                    print(f"  {key}: [{len(val)} items]")
                else:
                    print(f"  {key}: {val}")
except Exception as e:
    print(f"Error: {e}")

# 7. Probar diferentes formas de filtrar
print('\n=== 7. Probando filtros ===')

# 7a. POST con text search
print('\n7a. POST /api/users/search con text')
try:
    payload = {
        "Query": {
            "limit": 50,
            "text": "raul"
        }
    }
    resp = session.post(f"{host}/api/users/search", json=payload, headers=headers, verify=False, timeout=30)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        users = data.get('UserCollection', {}).get('rows', [])
        print(f"Usuarios: {len(users)}")
        for u in users[:5]:
            print(f"  {u.get('user_id')} - {u.get('name')}")
    else:
        print(f"Response: {resp.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

# 7b. POST con keyword
print('\n7b. POST /api/users/search con keyword')
try:
    payload = {
        "Query": {
            "limit": 50,
            "keyword": "raul"
        }
    }
    resp = session.post(f"{host}/api/users/search", json=payload, headers=headers, verify=False, timeout=30)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        users = data.get('UserCollection', {}).get('rows', [])
        print(f"Usuarios: {len(users)}")
        for u in users[:5]:
            print(f"  {u.get('user_id')} - {u.get('name')}")
    else:
        print(f"Response: {resp.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

# 7c. GET con text parameter
print('\n7c. GET /api/users?text=raul')
try:
    resp = session.get(f"{host}/api/users?text=raul&limit=50", headers=headers, verify=False, timeout=30)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        users = data.get('UserCollection', {}).get('rows', [])
        print(f"Usuarios: {len(users)}")
        for u in users[:5]:
            print(f"  {u.get('user_id')} - {u.get('name')}")
except Exception as e:
    print(f"Error: {e}")

# 7d. Filtrar en cliente (cargar todos y filtrar)
print('\n7d. Filtrar en cliente (buscar "raul" en 7192 usuarios)')
try:
    # Cargar todos los usuarios
    all_users = []
    offset = 0
    limit = 500
    while True:
        resp = session.get(f"{host}/api/users?limit={limit}&offset={offset}", headers=headers, verify=False, timeout=60)
        if resp.status_code != 200:
            break
        data = resp.json()
        users = data.get('UserCollection', {}).get('rows', [])
        if not users:
            break
        all_users.extend(users)
        offset += limit
        if offset >= 7200:  # Safety limit
            break
    
    print(f"Total usuarios cargados: {len(all_users)}")
    
    # Filtrar por nombre
    query = "raul"
    filtered = [u for u in all_users if query.lower() in (u.get('name') or '').lower() or query.lower() in str(u.get('user_id', '')).lower()]
    print(f"Usuarios con 'raul': {len(filtered)}")
    for u in filtered[:10]:
        print(f"  {u.get('user_id')} - {u.get('name')}")
except Exception as e:
    print(f"Error: {e}")

print('\n=== Fin de pruebas ===')
