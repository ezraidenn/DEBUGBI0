"""
Script principal para monitoreo y debugging de checadores BioStar.
"""
import sys
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.device_monitor import DeviceMonitor
from src.utils.logger import setup_logger
from src.utils.config import Config

# Configurar logger
logger = setup_logger(level="INFO")


def print_separator(char="=", length=80):
    """Imprime una línea separadora."""
    print(char * length)


def print_header(text: str):
    """Imprime un encabezado."""
    print_separator()
    print(f"  {text}")
    print_separator()


def list_devices(monitor: DeviceMonitor):
    """Lista todos los dispositivos/checadores."""
    print_header("📱 CHECADORES DISPONIBLES")
    
    devices = monitor.get_all_devices(refresh=True)
    
    if not devices:
        print("❌ No se encontraron dispositivos")
        return
    
    print(f"\nTotal: {len(devices)} checadores\n")
    
    for i, device in enumerate(devices, 1):
        device_id = device['id']
        device_name = device.get('name', 'Sin nombre')
        alias = device.get('alias', '')
        location = device.get('location', '')
        
        print(f"{i}. ID: {device_id}")
        print(f"   Nombre: {device_name}")
        if alias:
            print(f"   Alias: {alias}")
        if location:
            print(f"   Ubicación: {location}")
        print()


def show_device_debug(monitor: DeviceMonitor, device_id: int):
    """Muestra el debug del día de un dispositivo."""
    print_header(f"🔍 DEBUG DEL DÍA - Checador {device_id}")
    
    # Obtener información del dispositivo
    device = monitor.get_device_by_id(device_id)
    if device:
        print(f"\n📍 Dispositivo: {device.get('name', 'Sin nombre')}")
        if device.get('alias'):
            print(f"   Alias: {device['alias']}")
        if device.get('location'):
            print(f"   Ubicación: {device['location']}")
    
    # Obtener resumen
    summary = monitor.get_debug_summary(device_id)
    
    print(f"\n📊 Resumen del día ({datetime.now().strftime('%Y-%m-%d')}):")
    print(f"   Total de eventos: {summary['total_events']}")
    print(f"   Accesos concedidos: {summary['access_granted']}")
    print(f"   Accesos denegados: {summary['access_denied']}")
    print(f"   Usuarios únicos: {summary['unique_users']}")
    
    if summary['first_event']:
        print(f"   Primer evento: {summary['first_event'].strftime('%H:%M:%S')}")
    if summary['last_event']:
        print(f"   Último evento: {summary['last_event'].strftime('%H:%M:%S')}")
    
    if summary['total_events'] == 0:
        print("\n⚠️  No hay eventos registrados hoy")
        return
    
    # Preguntar si exportar
    print("\n¿Deseas exportar el debug completo a Excel? (s/n): ", end="")
    response = input().strip().lower()
    
    if response == 's':
        filename = monitor.export_daily_debug(device_id)
        if filename:
            print(f"\n✅ Debug exportado exitosamente: {filename}")


def assign_alias(monitor: DeviceMonitor):
    """Asigna un alias a un dispositivo."""
    print_header("✏️  ASIGNAR ALIAS A CHECADOR")
    
    # Listar dispositivos
    devices = monitor.get_all_devices()
    
    print("\nDispositivos disponibles:\n")
    for i, device in enumerate(devices, 1):
        device_id = device['id']
        device_name = device.get('name', 'Sin nombre')
        alias = device.get('alias', '')
        
        print(f"{i}. ID: {device_id} - {device_name}")
        if alias:
            print(f"   (Alias actual: {alias})")
    
    print("\nIngresa el número del dispositivo (0 para cancelar): ", end="")
    try:
        choice = int(input().strip())
        if choice == 0:
            return
        
        if 1 <= choice <= len(devices):
            device = devices[choice - 1]
            device_id = device['id']
            
            print(f"\n📝 Configurando alias para: {device.get('name', 'Sin nombre')}")
            print("   Alias (nombre personalizado): ", end="")
            alias = input().strip()
            
            print("   Ubicación (opcional): ", end="")
            location = input().strip()
            
            print("   Notas (opcional): ", end="")
            notes = input().strip()
            
            monitor.set_device_alias(device_id, alias, location, notes)
            print(f"\n✅ Alias asignado correctamente")
        else:
            print("❌ Opción inválida")
    except ValueError:
        print("❌ Entrada inválida")


def main_menu():
    """Menú principal."""
    # Inicializar monitor
    config = Config()
    monitor = DeviceMonitor(config)
    
    # Autenticar
    print_header("🔐 CONECTANDO A BIOSTAR 2")
    if not monitor.login():
        print("❌ Error al autenticar. Verifica las credenciales en .env")
        return
    
    print("✅ Conexión exitosa\n")
    
    while True:
        print_separator("-")
        print("\n🎯 MENÚ PRINCIPAL")
        print("\n1. Listar todos los checadores")
        print("2. Ver debug del día de un checador")
        print("3. Asignar alias a un checador")
        print("4. Exportar debug de todos los checadores")
        print("0. Salir")
        print("\nSelecciona una opción: ", end="")
        
        try:
            option = input().strip()
            
            if option == "0":
                print("\n👋 ¡Hasta luego!")
                break
            elif option == "1":
                list_devices(monitor)
            elif option == "2":
                print("\nIngresa el ID del checador: ", end="")
                device_id = int(input().strip())
                show_device_debug(monitor, device_id)
            elif option == "3":
                assign_alias(monitor)
            elif option == "4":
                print_header("📦 EXPORTANDO DEBUG DE TODOS LOS CHECADORES")
                devices = monitor.get_all_devices()
                for device in devices:
                    device_id = device['id']
                    device_name = device.get('alias') or device.get('name', f'Device_{device_id}')
                    print(f"\nExportando: {device_name}...")
                    monitor.export_daily_debug(device_id)
                print("\n✅ Exportación completada")
            else:
                print("❌ Opción inválida")
        except ValueError:
            print("❌ Entrada inválida")
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error fatal: {str(e)}")
        import traceback
        traceback.print_exc()
