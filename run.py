#!/usr/bin/env python3
"""
Script de inicio para la aplicacion DEBUGBI0.

Lee HOST/PORT/DEBUG de .env. En produccion usa waitress (Windows) o
gunicorn (Linux) detras de un reverse proxy con TLS.
"""
import os
import sys
from pathlib import Path

# Cargar variables de entorno antes de importar la app
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent / 'webapp'))


def _parse_bool(val, default=False):
    if val is None:
        return default
    return str(val).strip().lower() in ('true', '1', 'yes', 'on')


if __name__ == '__main__':
    from app import app, socketio

    host = os.environ.get('HOST', '127.0.0.1').strip()
    port = int(os.environ.get('PORT', 5000))
    debug = _parse_bool(os.environ.get('DEBUG'), default=False)
    flask_env = os.environ.get('FLASK_ENV', 'development').strip().lower()

    if flask_env == 'production' and debug:
        raise RuntimeError(
            "Refusing to start: DEBUG=true con FLASK_ENV=production. "
            "El debugger de Werkzeug es RCE-equivalente."
        )

    print("Iniciando servidor DEBUGBI0...")
    print(f"  Host:   {host}")
    print(f"  Port:   {port}")
    print(f"  Env:    {flask_env}")
    print(f"  Debug:  {debug}")
    print(f"  URL:    http://{host}:{port}")
    print("=" * 50)

    if flask_env == 'production':
        # Servir con waitress en Windows. En Linux preferir gunicorn.
        try:
            from waitress import serve
            print("[INFO] Sirviendo con waitress (produccion).")
            serve(app, host=host, port=port, threads=8, url_scheme='https')
        except ImportError:
            raise RuntimeError(
                "waitress no esta instalado. pip install waitress (o usa gunicorn en Linux)."
            )
    else:
        # Desarrollo: socketio.run con debug controlado por env.
        # NO usar allow_unsafe_werkzeug; bindear a 127.0.0.1 por defecto.
        socketio.run(app, debug=debug, host=host, port=port)
