"""
Script para probar obtención de eventos del usuario 8490
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
    print("PROBANDO OBTENCIÓN DE EVENTOS PARA USUARIO 8490")
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
    
    # Probar diferentes fechas
    fechas_a_probar = [
        datetime.now(MEXICO_TZ).date(),  # Hoy
        (datetime.now(MEXICO_TZ) - timedelta(days=1)).date(),  # Ayer
        (datetime.now(MEXICO_TZ) - timedelta(days=2)).date(),  # Anteayer
    ]
    
    for fecha in fechas_a_probar:
        print("\n" + "="*60)
        print(f"FECHA: {fecha}")
        print("="*60)
        
        inicio_dia = datetime.combine(fecha, datetime.min.time())
        fin_dia = datetime.combine(fecha, datetime.max.time())
        
        inicio_dia = MEXICO_TZ.localize(inicio_dia)
        fin_dia = MEXICO_TZ.localize(fin_dia)
        
        # Buscar eventos con user_id = "8490" (como string)
        conditions = [
            {
                "column": "user_id",
                "operator": 0,  # EQUAL
                "values": ["8490"]
            },
            {
                "column": "datetime",
                "operator": 5,  # GREATER_THAN_OR_EQUAL
                "values": [inicio_dia.strftime('%Y-%m-%dT%H:%M:%S')]
            },
            {
                "column": "datetime",
                "operator": 6,  # LESS_THAN_OR_EQUAL
                "values": [fin_dia.strftime('%Y-%m-%dT%H:%M:%S')]
            }
        ]
        
        print(f"Buscando eventos entre {inicio_dia} y {fin_dia}...")
        eventos = client.search_events(conditions=conditions, limit=1000, descending=False)
        
        print(f"Total de eventos: {len(eventos)}")
        
        if eventos:
            print("\n📋 EVENTOS ENCONTRADOS:")
            for i, evento in enumerate(eventos[:10], 1):
                print(f"\n  Evento {i}:")
                print(f"    Fecha/Hora: {evento.get('datetime')}")
                print(f"    Tipo: {evento.get('event_type', {}).get('name')}")
                print(f"    Código: {evento.get('event_type', {}).get('code')}")
                print(f"    Dispositivo: {evento.get('device', {}).get('name')}")
                print(f"    Usuario ID: {evento.get('user_id', {}).get('user_id')}")
            
            # Filtrar ACCESS_GRANTED (código 4864)
            eventos_granted = [
                e for e in eventos 
                if e.get('event_type', {}).get('code') == 4864
            ]
            
            print(f"\n✅ Eventos ACCESS_GRANTED: {len(eventos_granted)}")
            
            if eventos_granted:
                primer_evento = eventos_granted[0]
                print(f"\n🕐 PRIMER CHECK DEL DÍA:")
                print(f"   Hora: {primer_evento.get('datetime')}")
                print(f"   Dispositivo: {primer_evento.get('device', {}).get('name')}")
                
                # Parsear hora
                from dateutil import parser
                dt = parser.parse(primer_evento['datetime'])
                if dt.tzinfo is None:
                    dt = MEXICO_TZ.localize(dt)
                else:
                    dt = dt.astimezone(MEXICO_TZ)
                
                print(f"   Hora local: {dt.strftime('%H:%M:%S')}")
                
                # Comparar con hora esperada (09:00)
                hora_esperada = datetime.strptime('09:00:00', '%H:%M:%S').time()
                hora_limite = datetime.strptime('09:10:00', '%H:%M:%S').time()
                hora_check = dt.time()
                
                print(f"\n📊 ANÁLISIS:")
                print(f"   Hora esperada: {hora_esperada}")
                print(f"   Hora límite: {hora_limite}")
                print(f"   Hora de check: {hora_check}")
                
                if hora_check <= hora_limite:
                    print(f"   ✅ A TIEMPO")
                elif hora_check <= datetime.strptime('09:30:00', '%H:%M:%S').time():
                    print(f"   ⚠️ RETARDO")
                else:
                    print(f"   ❌ FALTA (llegada muy tarde)")
        else:
            print("  ⚠️ No hay eventos en esta fecha")
    
    print("\n" + "="*60)
    print("PRUEBAS COMPLETADAS")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
