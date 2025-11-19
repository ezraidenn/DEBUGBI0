"""
Script rápido para probar la conexión a BioStar.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.api.device_monitor import DeviceMonitor
from src.utils.logger import setup_logger

logger = setup_logger(level="INFO")


def main():
    print("="*60)
    print("🔍 TEST RÁPIDO - CONEXIÓN A BIOSTAR")
    print("="*60)
    
    # Crear monitor
    monitor = DeviceMonitor()
    
    # Probar autenticación
    print("\n1️⃣  Probando autenticación...")
    if not monitor.login():
        print("❌ Error al autenticar. Verifica las credenciales en .env")
        return
    
    print("✅ Autenticación exitosa")
    
    # Listar dispositivos
    print("\n2️⃣  Obteniendo lista de dispositivos...")
    devices = monitor.get_all_devices()
    
    if not devices:
        print("⚠️  No se encontraron dispositivos")
        return
    
    print(f"✅ {len(devices)} dispositivos encontrados\n")
    
    # Mostrar dispositivos
    print("📱 DISPOSITIVOS:")
    print("-" * 60)
    for i, device in enumerate(devices, 1):
        print(f"\n{i}. ID: {device['id']}")
        print(f"   Nombre: {device.get('name', 'Sin nombre')}")
        if device.get('alias'):
            print(f"   Alias: {device['alias']}")
        if device.get('location'):
            print(f"   Ubicación: {device['location']}")
    
    # Probar debug del primer dispositivo
    if devices:
        print("\n" + "="*60)
        print("3️⃣  Probando debug del primer dispositivo...")
        print("="*60)
        
        device_id = devices[0]['id']
        device_name = devices[0].get('name', 'Sin nombre')
        
        print(f"\nDispositivo: {device_name} (ID: {device_id})")
        
        summary = monitor.get_debug_summary(device_id)
        
        print(f"\n📊 Resumen del día:")
        print(f"   Total de eventos: {summary['total_events']}")
        print(f"   Accesos concedidos: {summary['access_granted']}")
        print(f"   Accesos denegados: {summary['access_denied']}")
        print(f"   Usuarios únicos: {summary['unique_users']}")
        
        if summary['first_event']:
            print(f"   Primer evento: {summary['first_event'].strftime('%H:%M:%S')}")
        if summary['last_event']:
            print(f"   Último evento: {summary['last_event'].strftime('%H:%M:%S')}")
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETADO EXITOSAMENTE")
    print("="*60)
    print("\n💡 Para usar el sistema completo, ejecuta: python src/main.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrumpido")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
