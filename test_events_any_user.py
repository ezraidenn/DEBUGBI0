"""
Script para probar obtención de eventos de cualquier usuario (últimos 7 días)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.biostar_client import BioStarAPIClient
from src.utils.config import Config
from datetime import datetime, timedelta
import pytz

MEXICO_TZ = pytz.timezone('America/Mexico_City')

def main():
    print("\n" + "="*60)
    print("PROBANDO OBTENCIÓN DE EVENTOS (ÚLTIMOS 7 DÍAS)")
    print("="*60)
    
    config = Config()
    biostar_cfg = config.biostar_config
    
    client = BioStarAPIClient(
        host=biostar_cfg['host'],
        username=biostar_cfg['username'],
        password=biostar_cfg['password']
    )
    
    if not client.login():
        print("❌ Error conectando con BioStar")
        return
    
    print("✅ Conectado a BioStar\n")
    
    # Buscar eventos de los últimos 7 días (cualquier usuario)
    inicio = datetime.now(MEXICO_TZ) - timedelta(days=7)
    fin = datetime.now(MEXICO_TZ)
    
    print(f"Buscando eventos entre {inicio} y {fin}...")
    
    conditions = [
        {
            "column": "datetime",
            "operator": 5,  # GREATER_THAN_OR_EQUAL
            "values": [inicio.strftime('%Y-%m-%dT%H:%M:%S')]
        },
        {
            "column": "datetime",
            "operator": 6,  # LESS_THAN_OR_EQUAL
            "values": [fin.strftime('%Y-%m-%dT%H:%M:%S')]
        }
    ]
    
    eventos = client.search_events(conditions=conditions, limit=100, descending=True)
    
    print(f"\nTotal de eventos encontrados: {len(eventos)}")
    
    if eventos:
        print("\n📋 PRIMEROS 10 EVENTOS:")
        usuarios_unicos = set()
        
        for i, evento in enumerate(eventos[:10], 1):
            user_info = evento.get('user_id', {})
            user_id = user_info.get('user_id', 'N/A')
            user_name = user_info.get('name', 'N/A')
            usuarios_unicos.add(user_id)
            
            print(f"\n  Evento {i}:")
            print(f"    Fecha/Hora: {evento.get('datetime')}")
            print(f"    Usuario ID: {user_id}")
            print(f"    Usuario Nombre: {user_name}")
            print(f"    Tipo: {evento.get('event_type', {}).get('name')}")
            print(f"    Código: {evento.get('event_type', {}).get('code')}")
            print(f"    Dispositivo: {evento.get('device', {}).get('name')}")
        
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   Usuarios únicos en muestra: {len(usuarios_unicos)}")
        print(f"   IDs: {list(usuarios_unicos)[:10]}")
        
        # Verificar si hay eventos del usuario 8490
        eventos_8490 = [e for e in eventos if e.get('user_id', {}).get('user_id') == '8490']
        print(f"\n   Eventos del usuario 8490 en últimos 7 días: {len(eventos_8490)}")
        
        if eventos_8490:
            print(f"\n   ✅ Usuario 8490 SÍ tiene eventos recientes:")
            for e in eventos_8490[:3]:
                print(f"      - {e.get('datetime')} | {e.get('event_type', {}).get('name')}")
    else:
        print("\n⚠️ No se encontraron eventos en los últimos 7 días")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
