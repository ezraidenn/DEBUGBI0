"""
Script para iniciar la aplicación web de BioStar Debug Monitor.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from webapp.app import app, socketio

if __name__ == '__main__':
    print("="*80)
    print("BIOSTAR DEBUG MONITOR - WEB APPLICATION (TIEMPO REAL)")
    print("="*80)
    print("\n[OK] Iniciando servidor web con WebSockets...")
    print("[OK] URL Local: http://localhost:5000")
    print("[OK] URL Red: http://10.0.0.10:5000")
    print("[OK] Usuario por defecto: admin")
    print("[OK] Contrasena por defecto: admin123")
    print("[OK] Tiempo Real: ACTIVADO")
    print("[OK] Permitiendo conexiones desde: 10.0.0.10")
    print("\n[INFO] Presiona Ctrl+C para detener el servidor\n")
    print("="*80)
    
    # Configurar para aceptar conexiones desde cualquier IP (incluyendo 10.0.0.10)
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
