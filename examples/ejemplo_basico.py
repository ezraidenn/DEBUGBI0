"""
Ejemplo básico de uso del monitor de dispositivos.
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.device_monitor import DeviceMonitor
from src.utils.logger import setup_logger

# Configurar logger
logger = setup_logger(level="INFO")


def ejemplo_listar_dispositivos():
    """Ejemplo: Listar todos los dispositivos/checadores."""
    print("="*60)
    print("EJEMPLO 1: Listar dispositivos")
    print("="*60)
    
    monitor = DeviceMonitor()
    
    # Autenticar
    if not monitor.login():
        print("Error al autenticar")
        return
    
    # Obtener dispositivos
    devices = monitor.get_all_devices()
    
    print(f"\n📱 Dispositivos encontrados: {len(devices)}\n")
    for device in devices:
        print(f"  ID: {device['id']:<10} | Nombre: {device['name']}")
        if device.get('alias'):
            print(f"                    | Alias: {device['alias']}")
        print()


def ejemplo_debug_del_dia():
    """Ejemplo: Obtener debug del día de un dispositivo."""
    print("="*60)
    print("EJEMPLO 2: Debug del día")
    print("="*60)
    
    monitor = DeviceMonitor()
    
    if not monitor.login():
        print("Error al autenticar")
        return
    
    # Obtener dispositivos
    devices = monitor.get_all_devices()
    
    if not devices:
        print("No se encontraron dispositivos")
        return
    
    # Usar el primer dispositivo como ejemplo
    device_id = devices[0]['id']
    device_name = devices[0]['name']
    
    print(f"\n🔍 Obteniendo debug del dispositivo:")
    print(f"   ID: {device_id}")
    print(f"   Nombre: {device_name}\n")
    
    # Obtener resumen
    summary = monitor.get_debug_summary(device_id)
    
    print("📊 Resumen del día:")
    print(f"   Total de eventos: {summary['total_events']}")
    print(f"   Accesos concedidos: {summary['access_granted']}")
    print(f"   Accesos denegados: {summary['access_denied']}")
    print(f"   Usuarios únicos: {summary['unique_users']}")
    
    if summary['total_events'] > 0:
        # Exportar a Excel
        print("\n📁 Exportando a Excel...")
        filename = monitor.export_daily_debug(device_id)
        print(f"✓ Archivo generado: {filename}")


def ejemplo_asignar_alias():
    """Ejemplo: Asignar alias a un dispositivo."""
    print("="*60)
    print("EJEMPLO 3: Asignar alias")
    print("="*60)
    
    monitor = DeviceMonitor()
    
    if not monitor.login():
        print("Error al autenticar")
        return
    
    # Obtener dispositivos
    devices = monitor.get_all_devices()
    
    if not devices:
        print("No se encontraron dispositivos")
        return
    
    # Asignar alias al primer dispositivo
    device_id = devices[0]['id']
    
    print(f"\n✏️  Asignando alias al dispositivo {device_id}...")
    
    monitor.set_device_alias(
        device_id=device_id,
        alias="Entrada Principal",
        location="Planta Baja",
        notes="Checador principal de acceso"
    )
    
    print("✓ Alias asignado correctamente")
    
    # Verificar
    device = monitor.get_device_by_id(device_id)
    print(f"\n📋 Información actualizada:")
    print(f"   ID: {device['id']}")
    print(f"   Nombre: {device['name']}")
    print(f"   Alias: {device['alias']}")
    print(f"   Ubicación: {device['location']}")
    print(f"   Notas: {device['notes']}")


def ejemplo_eventos_por_tipo():
    """Ejemplo: Obtener eventos específicos (solo accesos concedidos)."""
    print("="*60)
    print("EJEMPLO 4: Eventos por tipo")
    print("="*60)
    
    from datetime import datetime, timedelta
    
    monitor = DeviceMonitor()
    
    if not monitor.login():
        print("Error al autenticar")
        return
    
    devices = monitor.get_all_devices()
    if not devices:
        print("No se encontraron dispositivos")
        return
    
    device_id = devices[0]['id']
    
    # Obtener solo accesos concedidos del día
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    print(f"\n🔍 Obteniendo accesos concedidos del dispositivo {device_id}...")
    
    events = monitor.get_device_events_by_type(
        device_id=device_id,
        event_codes=["4864"],  # Código de acceso concedido
        start_date=today,
        end_date=tomorrow
    )
    
    print(f"✓ {len(events)} accesos concedidos encontrados")
    
    if events:
        df = monitor.events_to_dataframe(events)
        print("\n📋 Primeros 5 registros:")
        print(df[['datetime', 'user_name', 'event_type']].head())


def menu_ejemplos():
    """Menú de ejemplos."""
    while True:
        print("\n" + "="*60)
        print("EJEMPLOS DE USO - MONITOR DE CHECADORES")
        print("="*60)
        print("\n1. Listar dispositivos")
        print("2. Debug del día")
        print("3. Asignar alias a dispositivo")
        print("4. Eventos por tipo")
        print("0. Salir")
        print("\nSelecciona un ejemplo: ", end="")
        
        try:
            option = input().strip()
            
            if option == "0":
                break
            elif option == "1":
                ejemplo_listar_dispositivos()
            elif option == "2":
                ejemplo_debug_del_dia()
            elif option == "3":
                ejemplo_asignar_alias()
            elif option == "4":
                ejemplo_eventos_por_tipo()
            else:
                print("Opción inválida")
        except KeyboardInterrupt:
            print("\n\n¡Hasta luego!")
            break
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    menu_ejemplos()
