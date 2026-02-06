"""
Analizar estructura completa del evento de usuario 8490
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.biostar_client import BioStarAPIClient
from src.utils.config import Config
from datetime import datetime
import pytz
import json

MEXICO_TZ = pytz.timezone('America/Mexico_City')

def main():
    print("\n" + "="*60)
    print("ANALIZANDO ESTRUCTURA DEL EVENTO DE USUARIO 8490")
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
    
    hoy = datetime.now(MEXICO_TZ).date()
    inicio_dia = datetime.combine(hoy, datetime.min.time())
    fin_dia = datetime.combine(hoy, datetime.max.time())
    
    inicio_dia = MEXICO_TZ.localize(inicio_dia)
    fin_dia = MEXICO_TZ.localize(fin_dia)
    
    conditions = [
        {
            "column": "user_id.user_id",
            "operator": 0,
            "values": ["8490"]
        },
        {
            "column": "datetime",
            "operator": 3,
            "values": [
                inicio_dia.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                fin_dia.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            ]
        }
    ]
    
    eventos = client.search_events(conditions=conditions, limit=100, descending=False)
    
    print(f"Total de eventos encontrados: {len(eventos)}\n")
    
    if eventos:
        for i, evento in enumerate(eventos, 1):
            print("="*60)
            print(f"EVENTO {i} - ESTRUCTURA COMPLETA")
            print("="*60)
            print(json.dumps(evento, indent=2, ensure_ascii=False))
            print("\n")
            
            # Analizar campos específicos
            print("CAMPOS CLAVE:")
            print(f"  datetime: {evento.get('datetime')}")
            print(f"  event_type: {evento.get('event_type')}")
            print(f"  event_type_id: {evento.get('event_type_id')}")
            print(f"  event_code: {evento.get('event_code')}")
            print(f"  user_id: {evento.get('user_id')}")
            print(f"  device_id: {evento.get('device_id')}")
            
            # Buscar todos los campos que contengan 'code'
            print("\nCAMPOS CON 'code':")
            for key, value in evento.items():
                if 'code' in key.lower():
                    print(f"  {key}: {value}")
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        if 'code' in subkey.lower():
                            print(f"  {key}.{subkey}: {subvalue}")
            
            print("\n")
    else:
        print("⚠️ No se encontraron eventos")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
