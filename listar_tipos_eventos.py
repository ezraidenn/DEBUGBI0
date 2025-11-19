"""
Script para listar todos los tipos de eventos disponibles en BioStar.
Útil para conocer los códigos de eventos específicos de tu sistema.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.api.biostar_client import BioStarAPIClient
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(level="INFO")


def main():
    print("="*80)
    print("📋 TIPOS DE EVENTOS DISPONIBLES EN BIOSTAR")
    print("="*80)
    
    # Cargar configuración
    config = Config()
    biostar_cfg = config.biostar_config
    
    # Crear cliente
    client = BioStarAPIClient(
        host=biostar_cfg['host'],
        username=biostar_cfg['username'],
        password=biostar_cfg['password']
    )
    
    # Autenticar
    print("\n🔐 Autenticando...")
    if not client.login():
        print("❌ Error al autenticar. Verifica las credenciales en .env")
        return
    
    print("✅ Autenticación exitosa\n")
    
    # Obtener tipos de eventos
    print("📥 Obteniendo tipos de eventos...")
    event_types = client.get_event_types()
    
    if not event_types:
        print("❌ No se pudieron obtener los tipos de eventos")
        return
    
    print(f"✅ {len(event_types)} tipos de eventos encontrados\n")
    print("="*80)
    
    # Agrupar por categoría (basado en el código)
    categories = {
        'Acceso': [],
        'Puerta': [],
        'Usuario': [],
        'Dispositivo': [],
        'Sistema': [],
        'Otros': []
    }
    
    for event in event_types:
        code = event.get('code', '')
        name = event.get('name', 'Sin nombre')
        
        try:
            code_int = int(code)
            
            # Categorizar por rango de código
            if 4608 <= code_int <= 4999:
                categories['Acceso'].append((code, name))
            elif 20736 <= code_int <= 20999:
                categories['Puerta'].append((code, name))
            elif 12288 <= code_int <= 12999:
                categories['Usuario'].append((code, name))
            elif 28672 <= code_int <= 28999:
                categories['Dispositivo'].append((code, name))
            elif 32768 <= code_int <= 32999:
                categories['Sistema'].append((code, name))
            else:
                categories['Otros'].append((code, name))
        except ValueError:
            categories['Otros'].append((code, name))
    
    # Mostrar por categoría
    for category, events in categories.items():
        if events:
            print(f"\n{'='*80}")
            print(f"📂 {category.upper()} ({len(events)} eventos)")
            print('='*80)
            
            # Ordenar por código
            events.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 0)
            
            for code, name in events:
                print(f"  {code:<10} | {name}")
    
    # Exportar a archivo de texto
    output_file = "tipos_eventos_biostar.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("TIPOS DE EVENTOS BIOSTAR 2\n")
        f.write("="*80 + "\n\n")
        
        for category, events in categories.items():
            if events:
                f.write(f"\n{category.upper()} ({len(events)} eventos)\n")
                f.write("-"*80 + "\n")
                
                events.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 0)
                
                for code, name in events:
                    f.write(f"{code:<10} | {name}\n")
    
    print("\n" + "="*80)
    print(f"✅ Lista exportada a: {output_file}")
    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Operación cancelada")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
