"""
Script para buscar TODOS los eventos de hoy sin filtrar por usuario
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
    print("BUSCANDO TODOS LOS EVENTOS DE HOY")
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
    
    # Buscar eventos de HOY sin filtro de usuario
    hoy = datetime.now(MEXICO_TZ).date()
    inicio_dia = datetime.combine(hoy, datetime.min.time())
    fin_dia = datetime.combine(hoy, datetime.max.time())
    
    inicio_dia = MEXICO_TZ.localize(inicio_dia)
    fin_dia = MEXICO_TZ.localize(fin_dia)
    
    print(f"Fecha: {hoy}")
    print(f"Buscando eventos entre:")
    print(f"  Inicio: {inicio_dia}")
    print(f"  Fin: {fin_dia}\n")
    
    # Búsqueda 1: Solo con datetime (sin filtro de usuario)
    print("="*60)
    print("BÚSQUEDA 1: Solo datetime (BETWEEN)")
    print("="*60)
    
    conditions = [
        {
            "column": "datetime",
            "operator": 3,  # BETWEEN
            "values": [
                inicio_dia.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                fin_dia.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            ]
        }
    ]
    
    eventos = client.search_events(conditions=conditions, limit=100, descending=True)
    print(f"Total de eventos: {len(eventos)}\n")
    
    if eventos:
        print("PRIMEROS 5 EVENTOS:")
        for i, evento in enumerate(eventos[:5], 1):
            print(f"\n  Evento {i}:")
            print(f"    datetime: {evento.get('datetime')}")
            
            # Analizar estructura de user_id
            user_id_obj = evento.get('user_id')
            print(f"    user_id (tipo): {type(user_id_obj).__name__}")
            print(f"    user_id (valor): {user_id_obj}")
            
            if isinstance(user_id_obj, dict):
                print(f"    user_id.user_id: {user_id_obj.get('user_id')}")
                print(f"    user_id.name: {user_id_obj.get('name')}")
            
            event_type = evento.get('event_type', {})
            print(f"    event_type.code: {event_type.get('code')}")
            print(f"    event_type.name: {event_type.get('name')}")
        
        # Buscar específicamente el evento de raul cetina
        print("\n" + "="*60)
        print("BUSCANDO EVENTO DE RAUL CETINA (8490)")
        print("="*60)
        
        eventos_raul = []
        for e in eventos:
            user_id_obj = e.get('user_id')
            if isinstance(user_id_obj, dict):
                if user_id_obj.get('user_id') == '8490':
                    eventos_raul.append(e)
        
        print(f"Eventos de usuario 8490: {len(eventos_raul)}\n")
        
        if eventos_raul:
            print("EVENTOS DE RAUL CETINA:")
            for i, e in enumerate(eventos_raul, 1):
                print(f"\n  Evento {i}:")
                print(f"    datetime: {e.get('datetime')}")
                print(f"    user: {e.get('user_id', {}).get('name')}")
                print(f"    event: {e.get('event_type', {}).get('name')}")
        
        # Ahora probar búsqueda CON filtro de usuario
        print("\n" + "="*60)
        print("BÚSQUEDA 2: Con filtro user_id.user_id = '8490'")
        print("="*60)
        
        conditions_con_usuario = [
            {
                "column": "user_id.user_id",
                "operator": 0,  # EQUAL
                "values": ["8490"]
            },
            {
                "column": "datetime",
                "operator": 3,  # BETWEEN
                "values": [
                    inicio_dia.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    fin_dia.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                ]
            }
        ]
        
        eventos_filtrados = client.search_events(conditions=conditions_con_usuario, limit=100, descending=True)
        print(f"Total de eventos filtrados: {len(eventos_filtrados)}\n")
        
        if eventos_filtrados:
            print("EVENTOS FILTRADOS:")
            for i, e in enumerate(eventos_filtrados[:5], 1):
                print(f"\n  Evento {i}:")
                print(f"    datetime: {e.get('datetime')}")
                print(f"    user: {e.get('user_id', {}).get('name')}")
                print(f"    event: {e.get('event_type', {}).get('name')}")
        else:
            print("⚠️ No se encontraron eventos con el filtro de usuario")
            print("\nProbando diferentes variaciones del filtro...")
            
            # Probar sin el .user_id anidado
            print("\n  Variación 1: column='user_id'")
            conditions_v1 = [
                {
                    "column": "user_id",
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
            eventos_v1 = client.search_events(conditions=conditions_v1, limit=100)
            print(f"    Resultados: {len(eventos_v1)}")
            
            # Probar con user_id_id
            print("\n  Variación 2: column='user_id_id'")
            conditions_v2 = [
                {
                    "column": "user_id_id",
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
            eventos_v2 = client.search_events(conditions=conditions_v2, limit=100)
            print(f"    Resultados: {len(eventos_v2)}")
    
    else:
        print("⚠️ No se encontraron eventos de hoy")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
