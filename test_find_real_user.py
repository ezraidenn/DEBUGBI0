"""
Script para buscar usuarios reales en BioStar y probar con uno que exista
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.biostar_client import BioStarAPIClient
from src.utils.config import Config

def main():
    print("\n" + "="*60)
    print("BUSCANDO USUARIOS REALES EN BIOSTAR")
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
    
    # Obtener todos los usuarios
    usuarios = client.get_all_users(limit=1000)
    print(f"Total de usuarios: {len(usuarios)}\n")
    
    # Mostrar primeros 20 usuarios con sus IDs
    print("Primeros 20 usuarios:")
    print("-" * 60)
    for i, u in enumerate(usuarios[:20], 1):
        user_id = u.get('user_id', 'N/A')
        name = u.get('name', 'N/A')
        print(f"{i:2}. ID: {user_id:10} | Nombre: {name}")
    
    print("\n" + "="*60)
    print("Busca un usuario con ID numérico (ej: 2, 3, 4, etc.)")
    print("y úsalo para las pruebas de MobPer")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
