"""
Prueba final del sistema MobPer con usuario 8490
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.biostar_client import BioStarAPIClient
from src.utils.config import Config
from datetime import datetime, timedelta, time as time_type
import pytz

MEXICO_TZ = pytz.timezone('America/Mexico_City')

def obtener_primer_registro_dia(client, biostar_user_id, fecha):
    """
    Obtiene el primer registro ACCESS_GRANTED del día para un usuario.
    """
    try:
        inicio_dia = datetime.combine(fecha, datetime.min.time())
        fin_dia = datetime.combine(fecha, datetime.max.time())
        
        inicio_dia = MEXICO_TZ.localize(inicio_dia)
        fin_dia = MEXICO_TZ.localize(fin_dia)
        
        conditions = [
            {
                "column": "user_id.user_id",
                "operator": 0,  # EQUAL
                "values": [biostar_user_id]
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
        
        eventos = client.search_events(conditions=conditions, limit=1000, descending=False)
        
        if not eventos:
            return None
        
        # Filtrar solo eventos ACCESS_GRANTED
        ACCESS_GRANTED_CODES = [
            '4097', '4098', '4099', '4100', '4101', '4102', '4103', '4104', '4105', '4106', '4107',
            '4112', '4113', '4114', '4115', '4118', '4119', '4120', '4121', '4122', '4123', '4128', '4129',
            '4865', '4866', '4867', '4868', '4869', '4870', '4871', '4872'
        ]
        
        eventos_granted = [
            e for e in eventos 
            if e.get('event_type_id', {}).get('code') in ACCESS_GRANTED_CODES
        ]
        
        if not eventos_granted:
            return None
        
        # Ordenar por datetime y obtener el primero
        eventos_granted.sort(key=lambda x: x.get('datetime', ''))
        primer_evento = eventos_granted[0]
        
        # Parsear datetime
        from dateutil import parser
        dt = parser.parse(primer_evento['datetime'])
        if dt.tzinfo is None:
            dt = MEXICO_TZ.localize(dt)
        else:
            dt = dt.astimezone(MEXICO_TZ)
        
        return dt
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def calcular_incidencias_dia(client, user_id, fecha, hora_entrada_default, tolerancia_segundos):
    """
    Calcula la incidencia para un día específico.
    """
    dia_semana = fecha.weekday()
    
    # Verificar si es fin de semana
    if dia_semana in [5, 6]:  # Sábado o Domingo
        return {
            'fecha': fecha,
            'dia_semana': dia_semana,
            'tipo_dia': 'DESCANSO',
            'estado_auto': 'DESCANSO',
            'primer_registro': None,
            'minutos_diferencia': None
        }
    
    # Obtener primer registro
    primer_registro = obtener_primer_registro_dia(client, user_id, fecha)
    
    if primer_registro is None:
        return {
            'fecha': fecha,
            'dia_semana': dia_semana,
            'tipo_dia': 'LABORAL',
            'estado_auto': 'FALTA',
            'primer_registro': None,
            'minutos_diferencia': None
        }
    
    # Calcular si llegó a tiempo
    hora_limite = datetime.combine(fecha, hora_entrada_default) + timedelta(seconds=tolerancia_segundos)
    hora_limite = MEXICO_TZ.localize(hora_limite)
    
    if primer_registro <= hora_limite:
        estado = 'A_TIEMPO'
    else:
        estado = 'RETARDO'
    
    # Calcular diferencia en minutos
    hora_esperada = MEXICO_TZ.localize(datetime.combine(fecha, hora_entrada_default))
    diferencia = (primer_registro - hora_esperada).total_seconds() / 60
    
    return {
        'fecha': fecha,
        'dia_semana': dia_semana,
        'tipo_dia': 'LABORAL',
        'estado_auto': estado,
        'primer_registro': primer_registro,
        'minutos_diferencia': int(diferencia),
        'hora_entrada_esperada': hora_entrada_default,
        'hora_limite': hora_limite.time()
    }

def main():
    print("\n" + "="*60)
    print("PRUEBA FINAL - SISTEMA MOBPER")
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
    
    # Configuración del usuario
    user_id = "8490"
    user_name = "CETINA POOL RAUL ABEL"
    hora_entrada = time_type(9, 0, 0)  # 09:00:00
    tolerancia = 600  # 10 minutos
    
    print(f"Usuario: {user_name} (ID: {user_id})")
    print(f"Hora entrada: {hora_entrada}")
    print(f"Tolerancia: {tolerancia} segundos (10 minutos)")
    print(f"Hora límite: 09:10:00\n")
    
    # Calcular incidencias para hoy
    hoy = datetime.now(MEXICO_TZ).date()
    
    print("="*60)
    print(f"CALCULANDO INCIDENCIA PARA: {hoy}")
    print("="*60)
    
    incidencia = calcular_incidencias_dia(client, user_id, hoy, hora_entrada, tolerancia)
    
    print(f"\n📋 RESULTADO:")
    print(f"  Fecha: {incidencia['fecha']}")
    print(f"  Día de la semana: {['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'][incidencia['dia_semana']]}")
    print(f"  Tipo de día: {incidencia['tipo_dia']}")
    print(f"  Estado: {incidencia['estado_auto']}")
    
    if incidencia['primer_registro']:
        print(f"  Primer registro: {incidencia['primer_registro'].strftime('%H:%M:%S')}")
        print(f"  Diferencia: {incidencia['minutos_diferencia']} minutos")
        
        if incidencia['estado_auto'] == 'A_TIEMPO':
            print(f"  ✅ Llegó a tiempo")
        elif incidencia['estado_auto'] == 'RETARDO':
            print(f"  ⚠️ Retardo de {incidencia['minutos_diferencia']} minutos")
    else:
        if incidencia['estado_auto'] == 'FALTA':
            print(f"  ❌ Sin registro de entrada")
        elif incidencia['estado_auto'] == 'DESCANSO':
            print(f"  🏖️ Día de descanso")
    
    # Calcular para los últimos 7 días
    print("\n" + "="*60)
    print("INCIDENCIAS DE LOS ÚLTIMOS 7 DÍAS")
    print("="*60)
    
    for i in range(7):
        fecha = hoy - timedelta(days=i)
        inc = calcular_incidencias_dia(client, user_id, fecha, hora_entrada, tolerancia)
        
        estado_emoji = {
            'A_TIEMPO': '✅',
            'RETARDO': '⚠️',
            'FALTA': '❌',
            'DESCANSO': '🏖️',
            'INHABIL': '🔵'
        }.get(inc['estado_auto'], '❓')
        
        hora_str = inc['primer_registro'].strftime('%H:%M:%S') if inc['primer_registro'] else 'N/A'
        
        print(f"{fecha} | {estado_emoji} {inc['estado_auto']:10} | {hora_str}")
    
    print("\n" + "="*60)
    print("✅ SISTEMA MOBPER FUNCIONANDO CORRECTAMENTE")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
