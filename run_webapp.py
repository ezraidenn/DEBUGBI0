"""
Script para iniciar la aplicación web de BioStar Debug Monitor.
"""
import sys
import socket
from pathlib import Path
import io

# Force UTF-8 output to avoid cp1252 encoding errors on Windows consoles
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from webapp.app import app, socketio

def get_local_ip():
    """Obtiene la IP local de la red."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

if __name__ == '__main__':
    local_ip = get_local_ip()
    
    print("="*80)
    print("BIOSTAR DEBUG MONITOR - WEB APPLICATION (TIEMPO REAL)")
    print("="*80)
    print("\n[OK] Iniciando servidor web con WebSockets...")
    print("[OK] URL Local: http://localhost:5000")
    print(f"[OK] URL Red: http://{local_ip}:5000")
    print("[OK] Usuario por defecto: admin")
    print("[OK] Contrasena por defecto: admin123")
    print("[OK] Tiempo Real: ACTIVADO")
    print(f"[OK] Permitiendo conexiones desde: {local_ip}")
    print("\n[INFO] Presiona Ctrl+C para detener el servidor\n")
    print("="*80)
    
    # Configurar para aceptar conexiones desde cualquier IP
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
