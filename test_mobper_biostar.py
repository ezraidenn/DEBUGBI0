"""
Script de prueba para validar conexión con BioStar y funcionalidad de MobPer
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.biostar_client import BioStarAPIClient
from src.utils.config import Config
from datetime import datetime, date, timedelta
import pytz

MEXICO_TZ = pytz.timezone('America/Mexico_City')

def test_biostar_connection():
    """Prueba 1: Conexión básica con BioStar"""
    print("\n" + "="*60)
    print("PRUEBA 1: Conexión con BioStar")
    print("="*60)
    
    config = Config()
    biostar_cfg = config.biostar_config
    
    print(f"Host: {biostar_cfg['host']}")
    print(f"Usuario: {biostar_cfg['username']}")
    
    client = BioStarAPIClient(
        host=biostar_cfg['host'],
        username=biostar_cfg['username'],
        password=biostar_cfg['password']
    )
    
    if client.login():
        print("✅ Conexión exitosa con BioStar")
        return client
    else:
        print("❌ Error conectando con BioStar")
        return None

def test_find_user_by_code(client, user_code="8490"):
    """Prueba 2: Buscar usuario por código"""
    print("\n" + "="*60)
    print(f"PRUEBA 2: Buscar usuario con código {user_code}")
    print("="*60)
    
    if not client:
        print("❌ Cliente no disponible")
        return None
    
    try:
        usuarios = client.get_all_users()
        print(f"Total de usuarios en BioStar: {len(usuarios)}")
        
        # Buscar usuario específico
        usuario_encontrado = None
        for u in usuarios:
            if u.get('user_id') == user_code:
                usuario_encontrado = u
                break
        
        if usuario_encontrado:
            print(f"\n✅ Usuario encontrado:")
            print(f"   ID: {usuario_encontrado.get('user_id')}")
            print(f"   Nombre: {usuario_encontrado.get('name')}")
            print(f"   Email: {usuario_encontrado.get('email', 'N/A')}")
            print(f"   Departamento: {usuario_encontrado.get('department', 'N/A')}")
            return usuario_encontrado
        else:
            print(f"❌ Usuario {user_code} no encontrado")
            print(f"\nPrimeros 5 usuarios para referencia:")
            for u in usuarios[:5]:
                print(f"   - {u.get('user_id')}: {u.get('name')}")
            return None
            
    except Exception as e:
        print(f"❌ Error buscando usuario: {e}")
        return None

def test_name_validation(usuario, nombre_ingresado="Raul Cetina"):
    """Prueba 3: Validar coincidencia de nombre"""
    print("\n" + "="*60)
    print(f"PRUEBA 3: Validar nombre '{nombre_ingresado}'")
    print("="*60)
    
    if not usuario:
        print("❌ Usuario no disponible")
        return False
    
    nombre_biostar = usuario.get('name', '').lower()
    nombre_ingresado_lower = nombre_ingresado.lower()
    
    print(f"Nombre en BioStar: '{usuario.get('name')}'")
    print(f"Nombre ingresado: '{nombre_ingresado}'")
    
    # Verificar coincidencia
    palabras_biostar = nombre_biostar.split()
    palabras_ingresadas = nombre_ingresado_lower.split()
    
    print(f"\nPalabras en BioStar: {palabras_biostar}")
    print(f"Palabras ingresadas: {palabras_ingresadas}")
    
    if len(palabras_ingresadas) >= 2:
        primer_nombre = palabras_ingresadas[0]
        apellido = palabras_ingresadas[1]
        
        coincide_primer_nombre = primer_nombre in palabras_biostar
        coincide_apellido = apellido in palabras_biostar
        
        print(f"\n¿Coincide primer nombre '{primer_nombre}'? {coincide_primer_nombre}")
        print(f"¿Coincide apellido '{apellido}'? {coincide_apellido}")
        
        if coincide_primer_nombre and coincide_apellido:
            print("✅ Validación exitosa")
            return True
        else:
            print("❌ Validación fallida")
            return False
    else:
        print("❌ Se requieren al menos 2 palabras (nombre + apellido)")
        return False

def test_get_first_check_today(client, user_code="8490"):
    """Prueba 4: Obtener primer check del día"""
    print("\n" + "="*60)
    print(f"PRUEBA 4: Obtener primer check del día para usuario {user_code}")
    print("="*60)
    
    if not client:
        print("❌ Cliente no disponible")
        return None
    
    try:
        # Obtener fecha de hoy
        hoy = datetime.now(MEXICO_TZ).date()
        print(f"Fecha: {hoy}")
        
        # Calcular timestamps
        inicio_dia = datetime.combine(hoy, datetime.min.time())
        fin_dia = datetime.combine(hoy, datetime.max.time())
        
        inicio_dia = MEXICO_TZ.localize(inicio_dia)
        fin_dia = MEXICO_TZ.localize(fin_dia)
        
        print(f"Buscando eventos entre:")
        print(f"  Inicio: {inicio_dia}")
        print(f"  Fin: {fin_dia}")
        
        # Obtener eventos usando search_events con estructura correcta
        conditions = [
            {
                "column": "user_id.user_id",
                "operator": 0,  # EQUAL
                "values": [user_code]
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
        
        print(f"\nTotal de eventos encontrados: {len(eventos)}")
        
        if eventos:
            print("\nPrimeros 5 eventos:")
            for i, evento in enumerate(eventos[:5]):
                print(f"\n  Evento {i+1}:")
                print(f"    Fecha/Hora: {evento.get('datetime')}")
                print(f"    Tipo: {evento.get('event_type', {}).get('name')}")
                print(f"    Código: {evento.get('event_type', {}).get('code')}")
                print(f"    Dispositivo: {evento.get('device', {}).get('name')}")
            
            # Filtrar ACCESS_GRANTED
            eventos_granted = [
                e for e in eventos 
                if e.get('event_type', {}).get('code') == 4864
            ]
            
            print(f"\nEventos ACCESS_GRANTED: {len(eventos_granted)}")
            
            if eventos_granted:
                # Ordenar por fecha
                eventos_granted.sort(key=lambda x: x.get('datetime', ''))
                primer_evento = eventos_granted[0]
                
                print(f"\n✅ Primer check del día:")
                print(f"   Hora: {primer_evento.get('datetime')}")
                print(f"   Dispositivo: {primer_evento.get('device', {}).get('name')}")
                
                return primer_evento
            else:
                print("⚠️ No hay eventos ACCESS_GRANTED hoy")
                return None
        else:
            print("⚠️ No hay eventos para este usuario hoy")
            return None
            
    except Exception as e:
        print(f"❌ Error obteniendo eventos: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_get_check_specific_date(client, user_code="8490", fecha_str="2026-01-30"):
    """Prueba 5: Obtener primer check de una fecha específica"""
    print("\n" + "="*60)
    print(f"PRUEBA 5: Obtener primer check del {fecha_str} para usuario {user_code}")
    print("="*60)
    
    if not client:
        print("❌ Cliente no disponible")
        return None
    
    try:
        # Parsear fecha
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        print(f"Fecha: {fecha}")
        
        # Calcular timestamps
        inicio_dia = datetime.combine(fecha, datetime.min.time())
        fin_dia = datetime.combine(fecha, datetime.max.time())
        
        inicio_dia = MEXICO_TZ.localize(inicio_dia)
        fin_dia = MEXICO_TZ.localize(fin_dia)
        
        # Obtener eventos usando search_events con estructura correcta
        conditions = [
            {
                "column": "user_id.user_id",
                "operator": 0,  # EQUAL
                "values": [user_code]
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
        
        print(f"Total de eventos: {len(eventos)}")
        
        if eventos:
            # Filtrar ACCESS_GRANTED
            eventos_granted = [
                e for e in eventos 
                if e.get('event_type', {}).get('code') == 4864
            ]
            
            print(f"Eventos ACCESS_GRANTED: {len(eventos_granted)}")
            
            if eventos_granted:
                eventos_granted.sort(key=lambda x: x.get('datetime', ''))
                primer_evento = eventos_granted[0]
                
                print(f"\n✅ Primer check:")
                print(f"   Hora: {primer_evento.get('datetime')}")
                
                # Parsear hora
                from dateutil import parser
                dt = parser.parse(primer_evento['datetime'])
                if dt.tzinfo is None:
                    dt = MEXICO_TZ.localize(dt)
                else:
                    dt = dt.astimezone(MEXICO_TZ)
                
                print(f"   Hora local: {dt.strftime('%H:%M:%S')}")
                
                return primer_evento
            else:
                print("⚠️ No hay eventos ACCESS_GRANTED en esta fecha")
        else:
            print("⚠️ No hay eventos en esta fecha")
            
        return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Ejecutar todas las pruebas"""
    print("\n" + "="*60)
    print("PRUEBAS DE CONEXIÓN MOBPER - BIOSTAR")
    print("="*60)
    
    # Prueba 1: Conexión
    client = test_biostar_connection()
    if not client:
        print("\n❌ No se pudo conectar con BioStar. Verifica la configuración.")
        return
    
    # Prueba 2: Buscar usuario
    usuario = test_find_user_by_code(client, "8490")
    
    # Prueba 3: Validar nombre
    if usuario:
        test_name_validation(usuario, "Raul Cetina")
    
    # Prueba 4: Primer check de hoy
    test_get_first_check_today(client, "8490")
    
    # Prueba 5: Check de fecha específica (cambiar según necesites)
    test_get_check_specific_date(client, "8490", "2026-01-30")
    
    print("\n" + "="*60)
    print("PRUEBAS COMPLETADAS")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
