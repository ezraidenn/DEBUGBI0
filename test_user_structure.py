"""
Script para investigar la estructura real de los usuarios en BioStar
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.biostar_client import BioStarAPIClient
from src.utils.config import Config
import json

def main():
    print("\n" + "="*60)
    print("INVESTIGANDO ESTRUCTURA DE USUARIOS EN BIOSTAR")
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
    
    # Obtener primeros usuarios
    usuarios = client.get_all_users(limit=10)
    
    if not usuarios:
        print("❌ No se obtuvieron usuarios")
        return
    
    print(f"Total de usuarios obtenidos: {len(usuarios)}\n")
    
    # Mostrar estructura completa del primer usuario
    print("="*60)
    print("ESTRUCTURA COMPLETA DEL PRIMER USUARIO:")
    print("="*60)
    print(json.dumps(usuarios[0], indent=2, ensure_ascii=False))
    
    print("\n" + "="*60)
    print("CAMPOS DISPONIBLES EN USUARIOS:")
    print("="*60)
    for key in usuarios[0].keys():
        value = usuarios[0][key]
        tipo = type(value).__name__
        print(f"  {key:30} ({tipo:10}): {str(value)[:50]}")
    
    # Buscar usuario por nombre "raul" o "cetina"
    print("\n" + "="*60)
    print("BUSCANDO USUARIO 'RAUL CETINA':")
    print("="*60)
    
    # Buscar por nombre
    usuarios_raul = client.search_users("raul")
    print(f"\nResultados búsqueda 'raul': {len(usuarios_raul)}")
    
    for u in usuarios_raul[:5]:
        print(f"\n  Nombre: {u.get('name')}")
        print(f"  Campos disponibles:")
        for key, value in u.items():
            if 'id' in key.lower() or 'user' in key.lower():
                print(f"    {key}: {value}")
    
    # Buscar por "cetina"
    usuarios_cetina = client.search_users("cetina")
    print(f"\nResultados búsqueda 'cetina': {len(usuarios_cetina)}")
    
    for u in usuarios_cetina[:5]:
        print(f"\n  Nombre: {u.get('name')}")
        print(f"  Campos disponibles:")
        for key, value in u.items():
            if 'id' in key.lower() or 'user' in key.lower():
                print(f"    {key}: {value}")
    
    print("\n" + "="*60)
    print("ANÁLISIS COMPLETADO")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
