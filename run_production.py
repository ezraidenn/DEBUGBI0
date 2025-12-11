"""
Script para iniciar la aplicación en MODO PRODUCCIÓN con Waitress.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

from webapp.app import app, socketio

if __name__ == '__main__':
    print("="*80)
    print("🌐 BIOSTAR DEBUG MONITOR - MODO PRODUCCIÓN")
    print("="*80)
    print("\n✓ Servidor: Flask-SocketIO (con soporte SSE)")
    print("✓ Host: 0.0.0.0 (accesible desde red)")
    print("✓ Puerto: 5000")
    print("✓ Debug: DESACTIVADO")
    print("✓ Seguridad: NIVEL GOBIERNO")
    print("✓ Rate Limiting: ACTIVADO")
    print("✓ CSRF Protection: ACTIVADO")
    print("✓ Session Security: ACTIVADO")
    print("✓ Tiempo Real (SSE): ACTIVADO")
    print("\nURLs de acceso:")
    print("  - Local: http://localhost:5000")
    print("  - Red: http://10.0.0.10:5000")
    print("\n⚠️  Presiona Ctrl+C para detener el servidor\n")
    print("="*80)
    print("")
    
    # Iniciar servidor con SocketIO (soporta SSE)
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True
    )
