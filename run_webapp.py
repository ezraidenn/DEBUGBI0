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
    print("🌐 BIOSTAR DEBUG MONITOR - WEB APPLICATION (TIEMPO REAL)")
    print("="*80)
    print("\n✓ Iniciando servidor web con WebSockets...")
    print("✓ URL: http://localhost:5000")
    print("✓ Usuario por defecto: admin")
    print("✓ Contraseña por defecto: admin123")
    print("✓ Tiempo Real: ACTIVADO ⚡")
    print("\n⚠️  Presiona Ctrl+C para detener el servidor\n")
    print("="*80)
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
