"""
Script de prueba para verificar el monitor en tiempo real.
"""
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent))

from src.api.device_monitor import DeviceMonitor
from src.utils.config import Config

def test_monitor():
    print("="*80)
    print("🧪 TEST DE MONITOREO EN TIEMPO REAL")
    print("="*80)
    
    # Crear monitor
    config = Config()
    monitor = DeviceMonitor(config)
    
    # Autenticar
    print("\n1️⃣  Autenticando...")
    if not monitor.login():
        print("❌ Error al autenticar")
        return
    
    print("✅ Autenticación exitosa")
    
    # Obtener dispositivos
    print("\n2️⃣  Obteniendo dispositivos...")
    devices = monitor.get_all_devices(refresh=True)
    
    if not devices:
        print("❌ No se encontraron dispositivos")
        return
    
    print(f"✅ {len(devices)} dispositivos encontrados")
    
    # Usar el primer dispositivo
    device = devices[0]
    device_id = device['id']
    device_name = device['name']
    
    print(f"\n3️⃣  Monitoreando dispositivo:")
    print(f"   ID: {device_id}")
    print(f"   Nombre: {device_name}")
    
    # Obtener eventos iniciales
    print("\n4️⃣  Obteniendo eventos iniciales...")
    initial_events = monitor.get_device_events_today(device_id)
    initial_ids = set(e.get('id') for e in initial_events if e.get('id'))
    print(f"   Eventos iniciales: {len(initial_ids)}")
    
    # Monitorear por 30 segundos
    print("\n5️⃣  Monitoreando por 30 segundos...")
    print("   (Haz que alguien chequee en el dispositivo)")
    print()
    
    for i in range(15):  # 15 iteraciones de 2 segundos = 30 segundos
        time.sleep(2)
        
        # Obtener eventos actuales
        current_events = monitor.get_device_events_today(device_id)
        current_ids = set(e.get('id') for e in current_events if e.get('id'))
        
        # Detectar nuevos
        new_ids = current_ids - initial_ids
        
        if new_ids:
            print(f"\n🔔 NUEVO EVENTO DETECTADO!")
            new_events = [e for e in current_events if e.get('id') in new_ids]
            for event in new_events:
                print(f"   - ID: {event.get('id')}")
                print(f"   - Usuario: {event.get('user_id', {}).get('name', 'Desconocido')}")
                print(f"   - Tipo: {event.get('event_type_id', {}).get('name', 'Evento')}")
                print(f"   - Fecha: {event.get('datetime')}")
            
            # Actualizar IDs conocidos
            initial_ids = current_ids
        else:
            print(f"   [{i+1}/15] Sin nuevos eventos... ({(i+1)*2}s)", end='\r')
    
    print("\n\n✅ Test completado")
    print("="*80)


if __name__ == "__main__":
    try:
        test_monitor()
    except KeyboardInterrupt:
        print("\n\n⏸ Test interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
