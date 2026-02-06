"""
Script para buscar a Raul Cetina (ID 8490) iterando sobre todos los usuarios
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.biostar_client import BioStarAPIClient
from src.utils.config import Config
import json

def main():
    print("\n" + "="*60)
    print("BUSCANDO USUARIO 8490 (RAUL CETINA)")
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
    
    # Obtener TODOS los usuarios (aumentar límite)
    print("Obteniendo usuarios de BioStar...")
    usuarios = client.get_all_users(limit=2000)
    print(f"Total de usuarios obtenidos: {len(usuarios)}\n")
    
    # Buscar usuario con user_id = "8490"
    print("Buscando usuario con user_id = '8490'...")
    usuario_8490 = None
    
    for u in usuarios:
        if u.get('user_id') == "8490":
            usuario_8490 = u
            break
    
    if usuario_8490:
        print("\n✅ USUARIO ENCONTRADO!")
        print("="*60)
        print(json.dumps(usuario_8490, indent=2, ensure_ascii=False))
        print("="*60)
        
        print("\n📋 RESUMEN:")
        print(f"  user_id: {usuario_8490.get('user_id')}")
        print(f"  name: {usuario_8490.get('name')}")
        print(f"  login_id: {usuario_8490.get('login_id')}")
        
        # Validar nombre
        nombre_biostar = usuario_8490.get('name', '').lower()
        print(f"\n🔍 Validación de nombre:")
        print(f"  Nombre en BioStar: '{usuario_8490.get('name')}'")
        print(f"  Palabras: {nombre_biostar.split()}")
        
        # Probar validación
        nombre_test = "Raul Cetina"
        palabras_test = nombre_test.lower().split()
        print(f"\n  Nombre a validar: '{nombre_test}'")
        print(f"  Palabras: {palabras_test}")
        
        if len(palabras_test) >= 2:
            primer_nombre = palabras_test[0]
            apellido = palabras_test[1]
            
            coincide_nombre = primer_nombre in nombre_biostar.split()
            coincide_apellido = apellido in nombre_biostar.split()
            
            print(f"\n  ¿'{primer_nombre}' en BioStar? {coincide_nombre}")
            print(f"  ¿'{apellido}' en BioStar? {coincide_apellido}")
            
            if coincide_nombre and coincide_apellido:
                print("\n  ✅ VALIDACIÓN EXITOSA")
            else:
                print("\n  ❌ VALIDACIÓN FALLIDA")
    else:
        print("\n❌ Usuario 8490 NO encontrado")
        print("\nMostrando algunos user_ids para referencia:")
        for u in usuarios[:20]:
            print(f"  user_id: {u.get('user_id'):10} | name: {u.get('name')}")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
