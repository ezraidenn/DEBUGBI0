"""
Script de prueba para exportar debug de un checador.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.api.device_monitor import DeviceMonitor
from src.utils.logger import setup_logger

logger = setup_logger(level="INFO")


def main():
    print("="*80)
    print("🧪 TEST DE EXPORTACIÓN DE DEBUG")
    print("="*80)
    
    # Crear monitor
    monitor = DeviceMonitor()
    
    # Autenticar
    print("\n1️⃣  Autenticando...")
    if not monitor.login():
        print("❌ Error al autenticar")
        return
    
    print("✅ Autenticación exitosa")
    
    # Obtener dispositivos
    print("\n2️⃣  Obteniendo dispositivos...")
    devices = monitor.get_all_devices()
    
    if not devices:
        print("❌ No se encontraron dispositivos")
        return
    
    print(f"✅ {len(devices)} dispositivos encontrados")
    
    # Usar el primer dispositivo
    device = devices[0]
    device_id = device['id']
    device_name = device['name']
    
    print(f"\n3️⃣  Exportando debug del dispositivo:")
    print(f"   ID: {device_id}")
    print(f"   Nombre: {device_name}")
    
    # Obtener resumen primero
    summary = monitor.get_debug_summary(device_id)
    print(f"\n📊 Resumen:")
    print(f"   Total de eventos: {summary['total_events']}")
    print(f"   Accesos concedidos: {summary['access_granted']}")
    print(f"   Accesos denegados: {summary['access_denied']}")
    print(f"   Usuarios únicos: {summary['unique_users']}")
    
    if summary['total_events'] == 0:
        print("\n⚠️  No hay eventos del día para exportar")
        return
    
    # Exportar
    print("\n4️⃣  Generando archivo Excel...")
    filename = monitor.export_daily_debug(device_id)
    
    if filename:
        print(f"\n✅ ÉXITO: Archivo generado en:")
        print(f"   {filename}")
        
        # Verificar que el archivo existe
        if Path(filename).exists():
            size = Path(filename).stat().st_size
            print(f"   Tamaño: {size:,} bytes")
        
        print("\n💡 Abre el archivo Excel para ver:")
        print("   • Hoja 'Eventos': Todos los eventos del día")
        print("   • Hoja 'Resumen': Estadísticas generales")
        print("   • Hoja 'Por Tipo': Conteo por tipo de evento")
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETADO")
    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
