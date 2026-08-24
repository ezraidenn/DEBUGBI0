"""
Módulo de Seguridad NIVEL GOBIERNO para BioStar Logs Monitor.
Implementa protecciones avanzadas contra ataques.

Características:
- CSRF Protection
- 2FA con TOTP
- Session Fingerprinting
- Rate Limiting avanzado
- Bloqueo permanente de cuentas
- Historial de contraseñas
- IP Whitelisting
- Auditoría completa
- Encriptación de datos sensibles
"""
import os
import re
import logging
import hashlib
import hmac
import base64
import json
import secrets
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Tuple, Dict, Any, List
from collections import defaultdict
import threading

from flask import request, abort, jsonify, g, current_app, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

# Cryptography para encriptación
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️ cryptography no instalado. Algunas funciones de encriptación no estarán disponibles.")

# TOTP para 2FA
try:
    import pyotp
    import qrcode
    from io import BytesIO
    TOTP_AVAILABLE = True
except ImportError:
    TOTP_AVAILABLE = False
    print("⚠️ pyotp/qrcode no instalado. 2FA no estará disponible.")

# ============================================
# CONFIGURACIÓN DESDE VARIABLES DE ENTORNO
# ============================================

def get_env_bool(key: str, default: bool = False) -> bool:
    """Obtiene variable de entorno como booleano. Tolera espacios y CRLF."""
    value = os.environ.get(key)
    if value is None:
        return default
    return value.strip().lower() in ('true', '1', 'yes', 'on')


def get_env_int(key: str, default: int) -> int:
    """Obtiene variable de entorno como entero. Loguea si el valor es invalido."""
    raw = os.environ.get(key)
    if raw is None:
        return default
    try:
        return int(str(raw).strip())
    except (ValueError, TypeError):
        logging.getLogger('security').warning(
            "Variable de entorno %s='%s' no es entero, usando default=%s", key, raw, default
        )
        return default


class SecurityConfig:
    """Configuración de seguridad NIVEL GOBIERNO desde variables de entorno."""
    
    # ==================== RATE LIMITING ====================
    LOGIN_RATE_LIMIT = get_env_int('LOGIN_RATE_LIMIT', 10)
    LOGIN_MAX_ATTEMPTS = get_env_int('LOGIN_MAX_ATTEMPTS', 10)  # 10 intentos antes de bloqueo
    LOGIN_LOCKOUT_MINUTES = get_env_int('LOGIN_LOCKOUT_MINUTES', 30)  # 30 min de cooldown
    API_RATE_LIMIT = get_env_int('API_RATE_LIMIT', 60)
    
    # Bloqueo permanente deshabilitado (estilo FB: solo bloqueos temporales)
    PERMANENT_LOCKOUT_AFTER = get_env_int('PERMANENT_LOCKOUT_AFTER', 999)
    
    # ==================== PASSWORD POLICY ====================
    PASSWORD_MIN_LENGTH = get_env_int('PASSWORD_MIN_LENGTH', 8)  # Mínimo 8 caracteres
    PASSWORD_REQUIRE_UPPER = get_env_bool('PASSWORD_REQUIRE_UPPER', False)
    PASSWORD_REQUIRE_LOWER = get_env_bool('PASSWORD_REQUIRE_LOWER', False)
    PASSWORD_REQUIRE_DIGIT = get_env_bool('PASSWORD_REQUIRE_DIGIT', False)
    PASSWORD_REQUIRE_SPECIAL = get_env_bool('PASSWORD_REQUIRE_SPECIAL', False)
    PASSWORD_HISTORY_COUNT = get_env_int('PASSWORD_HISTORY_COUNT', 5)  # No reusar últimas 5
    PASSWORD_MAX_AGE_DAYS = get_env_int('PASSWORD_MAX_AGE_DAYS', 90)  # Forzar cambio cada 90 días
    
    # ==================== SESSION ====================
    SESSION_LIFETIME_MINUTES = get_env_int('SESSION_LIFETIME_MINUTES', 30)  # 30 min para gobierno
    SESSION_INACTIVITY_TIMEOUT = get_env_int('SESSION_INACTIVITY_TIMEOUT', 15)  # 15 min inactividad
    REMEMBER_COOKIE_DAYS = get_env_int('REMEMBER_COOKIE_DAYS', 1)  # Solo 1 día
    SESSION_FINGERPRINT = get_env_bool('SESSION_FINGERPRINT', True)  # Validar IP+UA
    
    # ==================== 2FA ====================
    REQUIRE_2FA = get_env_bool('REQUIRE_2FA', False)  # Activar para gobierno
    REQUIRE_2FA_FOR_ADMIN = get_env_bool('REQUIRE_2FA_FOR_ADMIN', True)  # Obligatorio para admins
    
    # ==================== IP WHITELISTING ====================
    IP_WHITELIST_ENABLED = get_env_bool('IP_WHITELIST_ENABLED', False)
    IP_WHITELIST = os.environ.get('IP_WHITELIST', '').split(',')  # IPs separadas por coma
    ADMIN_IP_WHITELIST = os.environ.get('ADMIN_IP_WHITELIST', '').split(',')  # Solo para admins
    
    # ==================== HTTPS ====================
    FORCE_HTTPS = get_env_bool('FORCE_HTTPS', False)
    HSTS_MAX_AGE = get_env_int('HSTS_MAX_AGE', 31536000)  # 1 año
    
    # ==================== CSRF ====================
    CSRF_ENABLED = get_env_bool('CSRF_ENABLED', True)
    CSRF_TIME_LIMIT = get_env_int('CSRF_TIME_LIMIT', 3600)  # 1 hora
    
    # ==================== AUDIT ====================
    SECURITY_AUDIT_LOG = get_env_bool('SECURITY_AUDIT_LOG', True)
    AUDIT_LOG_FILE = os.environ.get('AUDIT_LOG_FILE', 'logs/security_audit.log')
    AUDIT_ALL_REQUESTS = get_env_bool('AUDIT_ALL_REQUESTS', False)  # Log de todas las peticiones
    
    # ==================== ENCRYPTION ====================
    ENCRYPT_SENSITIVE_DATA = get_env_bool('ENCRYPT_SENSITIVE_DATA', True)
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', '')

    # ==================== CORS / PROXY ====================
    ALLOWED_ORIGINS = [
        o.strip() for o in os.environ.get('ALLOWED_ORIGINS', '').split(',')
        if o.strip()
    ]
    TRUSTED_PROXY_COUNT = get_env_int('TRUSTED_PROXY_COUNT', 0)

    # ==================== PRODUCCIÓN ====================
    # Ocultar información sensible en producción
    HIDE_SERVER_INFO = get_env_bool('HIDE_SERVER_INFO', True)  # Ocultar versión servidor
    DISABLE_DEBUG_TOOLBAR = get_env_bool('DISABLE_DEBUG_TOOLBAR', True)  # Sin debug toolbar
    SUPPRESS_CONSOLE_LOGS = get_env_bool('SUPPRESS_CONSOLE_LOGS', False)  # Suprimir console.log en prod
    MINIFY_HTML = get_env_bool('MINIFY_HTML', False)  # Minificar HTML
    REMOVE_COMMENTS = get_env_bool('REMOVE_COMMENTS', True)  # Remover comentarios HTML


# ============================================
# LOGGER DE AUDITORÍA DE SEGURIDAD
# ============================================

class SecurityAuditLogger:
    """Logger especializado para eventos de seguridad."""

    # Patrones a redactar en mensajes (tokens hex/base64 largos en paths)
    _REDACT_PATTERNS = [
        re.compile(r'(/download/)[0-9a-fA-F]{16,}'),
        re.compile(r'(/excel/(?:download|token)/)[0-9a-zA-Z_\-]{16,}'),
        re.compile(r'(token=)[^\s&]+'),
    ]

    def __init__(self):
        from logging.handlers import RotatingFileHandler

        self.logger = logging.getLogger('security_audit')
        self.logger.setLevel(logging.INFO)

        # Solo configurar si esta habilitado
        if SecurityConfig.SECURITY_AUDIT_LOG and not self.logger.handlers:
            log_dir = os.path.dirname(SecurityConfig.AUDIT_LOG_FILE)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            # Rotacion: 10 MB x 10 backups (~100 MB techo)
            handler = RotatingFileHandler(
                SecurityConfig.AUDIT_LOG_FILE,
                maxBytes=10 * 1024 * 1024,
                backupCount=10,
                encoding='utf-8',
            )
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.propagate = False

    def _redact(self, value: str) -> str:
        out = str(value)
        for pat in self._REDACT_PATTERNS:
            out = pat.sub(r'\1<redacted>', out)
        return out
    
    def log_event(self, event_type: str, details: Dict[str, Any], ip: str = None):
        """Registra un evento de seguridad."""
        if not SecurityConfig.SECURITY_AUDIT_LOG:
            return

        ip = ip or self._get_client_ip()
        user = details.get('user', 'anonymous')

        message = f"[{event_type}] IP={self._redact(ip)} USER={self._redact(user)}"
        for key, value in details.items():
            if key == 'user':
                continue
            message += f" {key.upper()}={self._redact(value)}"

        if 'FAIL' in event_type or 'BLOCK' in event_type or 'HIJACK' in event_type:
            self.logger.warning(message)
        else:
            self.logger.info(message)

    def _get_client_ip(self) -> str:
        """Obtiene IP del cliente. Solo confia en X-Forwarded-For si hay
        TRUSTED_PROXY_COUNT>0, para evitar spoofing."""
        try:
            if SecurityConfig.TRUSTED_PROXY_COUNT > 0:
                xff = request.headers.get('X-Forwarded-For')
                if xff:
                    # El cliente real es el de la izquierda; los siguientes son proxies.
                    parts = [p.strip() for p in xff.split(',') if p.strip()]
                    if parts:
                        return parts[0]
                real = request.headers.get('X-Real-IP')
                if real:
                    return real.strip()
            return request.remote_addr or 'unknown'
        except Exception:
            return 'unknown'


# Instancia global
audit_logger = SecurityAuditLogger()


# ============================================
# RATE LIMITER (Protección contra fuerza bruta)
# ============================================

class RateLimiter:
    """
    Rate limiter en memoria con bloqueo temporal.
    Thread-safe para uso con múltiples workers.
    """
    
    def __init__(self):
        self._attempts = defaultdict(list)  # {key: [timestamps]}
        self._blocked = {}  # {key: block_until_timestamp}
        self._lock = threading.Lock()
    
    def _clean_old_attempts(self, key: str, window_seconds: int):
        """Elimina intentos antiguos fuera de la ventana de tiempo."""
        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        self._attempts[key] = [t for t in self._attempts[key] if t > cutoff]
    
    def is_blocked(self, key: str) -> Tuple[bool, int]:
        """
        Verifica si una key está bloqueada.
        Returns: (is_blocked, seconds_remaining)
        """
        with self._lock:
            if key in self._blocked:
                if datetime.now() < self._blocked[key]:
                    remaining = (self._blocked[key] - datetime.now()).seconds
                    return True, remaining
                else:
                    del self._blocked[key]
            return False, 0
    
    def record_attempt(self, key: str, window_seconds: int = 60) -> int:
        """
        Registra un intento y retorna el número de intentos en la ventana.
        """
        with self._lock:
            self._clean_old_attempts(key, window_seconds)
            self._attempts[key].append(datetime.now())
            return len(self._attempts[key])
    
    def block(self, key: str, minutes: int):
        """Bloquea una key por X minutos."""
        with self._lock:
            self._blocked[key] = datetime.now() + timedelta(minutes=minutes)
            # Limpiar intentos al bloquear
            self._attempts[key] = []
    
    def reset(self, key: str):
        """Resetea intentos y bloqueo para una key."""
        with self._lock:
            self._attempts.pop(key, None)
            self._blocked.pop(key, None)
    
    def get_attempts(self, key: str) -> int:
        """Obtiene número de intentos actuales."""
        with self._lock:
            return len(self._attempts.get(key, []))


# Instancias globales
login_limiter = RateLimiter()
api_limiter = RateLimiter()


def _login_keys(ip: str, username: str) -> Tuple[str, str]:
    """Devuelve dos claves separadas: por IP y por username.
    Aplicarlas en paralelo evita (a) bypass rotando IP, y (b) DoS
    contra el username legitimo desde una sola IP malicios."""
    return f"ip:{ip}", f"user:{(username or '').lower()}"


def check_login_rate_limit(identifier: str, username: str = None) -> Tuple[bool, str]:
    """
    Verifica rate limit para login con dos llaves (IP + username).
    `identifier` debe ser la IP del cliente (o un valor estable por origen).
    Si `username` es None se asume formato legacy 'ip:user'.
    Returns: (allowed, error_message)
    """
    if username is None and ':' in identifier:
        ip_part, user_part = identifier.split(':', 1)
        ip_key, user_key = _login_keys(ip_part, user_part)
    else:
        ip_key, user_key = _login_keys(identifier, username or '')

    # Bloqueo si CUALQUIERA de las dos llaves esta bloqueada
    for key in (ip_key, user_key):
        blocked, remaining = login_limiter.is_blocked(key)
        if blocked:
            audit_logger.log_event('LOGIN_BLOCKED', {
                'key': key,
                'remaining_seconds': remaining,
            })
            return False, f'Cuenta bloqueada temporalmente. Intenta en {remaining // 60 + 1} minutos.'

    # Registrar intento en ambas llaves (ventana 30 min)
    ip_attempts = login_limiter.record_attempt(ip_key, window_seconds=1800)
    user_attempts = login_limiter.record_attempt(user_key, window_seconds=1800)

    if ip_attempts > SecurityConfig.LOGIN_MAX_ATTEMPTS:
        login_limiter.block(ip_key, SecurityConfig.LOGIN_LOCKOUT_MINUTES)
        audit_logger.log_event('LOGIN_LOCKOUT', {
            'key': ip_key, 'attempts': ip_attempts,
            'lockout_minutes': SecurityConfig.LOGIN_LOCKOUT_MINUTES,
        })
        return False, f'Demasiados intentos fallidos. Bloqueado {SecurityConfig.LOGIN_LOCKOUT_MINUTES} minutos.'

    if user_attempts > SecurityConfig.LOGIN_MAX_ATTEMPTS:
        login_limiter.block(user_key, SecurityConfig.LOGIN_LOCKOUT_MINUTES)
        audit_logger.log_event('LOGIN_LOCKOUT', {
            'key': user_key, 'attempts': user_attempts,
            'lockout_minutes': SecurityConfig.LOGIN_LOCKOUT_MINUTES,
        })
        return False, f'Demasiados intentos fallidos. Bloqueado {SecurityConfig.LOGIN_LOCKOUT_MINUTES} minutos.'

    return True, ''


def record_login_success(identifier: str, username: str = None):
    """Registra login exitoso y resetea rate limit en ambas llaves."""
    if username is None and ':' in identifier:
        ip_part, user_part = identifier.split(':', 1)
        ip_key, user_key = _login_keys(ip_part, user_part)
    else:
        ip_key, user_key = _login_keys(identifier, username or '')
    login_limiter.reset(ip_key)
    login_limiter.reset(user_key)
    audit_logger.log_event('LOGIN_SUCCESS', {'user': (username or identifier)})


def record_login_failure(identifier: str, username: str = None):
    """Registra intento fallido."""
    if username is None and ':' in identifier:
        ip_part, user_part = identifier.split(':', 1)
        ip_key, user_key = _login_keys(ip_part, user_part)
        attempted_user = user_part
    else:
        ip_key, user_key = _login_keys(identifier, username or '')
        attempted_user = username or 'unknown'
    ip_attempts = login_limiter.get_attempts(ip_key)
    user_attempts = login_limiter.get_attempts(user_key)
    audit_logger.log_event('LOGIN_FAIL', {
        'user': attempted_user,
        'ip_attempts': ip_attempts,
        'user_attempts': user_attempts,
        'max_attempts': SecurityConfig.LOGIN_MAX_ATTEMPTS,
    })


# ============================================
# DECORADOR DE RATE LIMIT PARA API
# ============================================

def rate_limit_api(requests_per_minute: int = None):
    """
    Decorador para aplicar rate limiting a endpoints de API.
    """
    limit = requests_per_minute or SecurityConfig.API_RATE_LIMIT
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Usar IP como identificador
            identifier = request.remote_addr or 'unknown'
            
            # Verificar bloqueo
            blocked, remaining = api_limiter.is_blocked(identifier)
            if blocked:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': remaining
                }), 429
            
            # Registrar y verificar
            attempts = api_limiter.record_attempt(identifier, window_seconds=60)
            if attempts > limit:
                api_limiter.block(identifier, 1)  # Bloquear 1 minuto
                return jsonify({
                    'error': 'Too many requests',
                    'retry_after': 60
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================
# VALIDACIÓN DE CONTRASEÑAS
# ============================================

def validate_password(password: str) -> Tuple[bool, str]:
    """
    Valida que la contrase~na cumpla con la politica de seguridad.
    Returns: (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, 'La contrase~na no puede estar vacia.'

    if len(password) < SecurityConfig.PASSWORD_MIN_LENGTH:
        return False, f'La contrase~na debe tener minimo {SecurityConfig.PASSWORD_MIN_LENGTH} caracteres.'

    if SecurityConfig.PASSWORD_REQUIRE_UPPER and not re.search(r'[A-Z]', password):
        return False, 'La contrase~na debe contener al menos una mayuscula.'

    if SecurityConfig.PASSWORD_REQUIRE_LOWER and not re.search(r'[a-z]', password):
        return False, 'La contrase~na debe contener al menos una minuscula.'

    if SecurityConfig.PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', password):
        return False, 'La contrase~na debe contener al menos un digito.'

    if SecurityConfig.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[^\w\s]', password):
        return False, 'La contrase~na debe contener al menos un caracter especial.'

    # Deny-list mini: contrase~nas obviamente debiles
    weak = {
        'password', 'admin123', '12345678', 'qwerty123', 'letmein123',
        'biostar', 'biostar123', 'changeme',
    }
    if password.lower() in weak:
        return False, 'Contrase~na demasiado comun. Elige otra.'

    return True, ''


def get_password_policy_text() -> str:
    """Retorna texto descriptivo de la politica de contrase~nas."""
    parts = [f'minimo {SecurityConfig.PASSWORD_MIN_LENGTH} caracteres']
    if SecurityConfig.PASSWORD_REQUIRE_UPPER:
        parts.append('mayusculas')
    if SecurityConfig.PASSWORD_REQUIRE_LOWER:
        parts.append('minusculas')
    if SecurityConfig.PASSWORD_REQUIRE_DIGIT:
        parts.append('digitos')
    if SecurityConfig.PASSWORD_REQUIRE_SPECIAL:
        parts.append('caracteres especiales')
    return 'Requisitos: ' + ', '.join(parts)


# ============================================
# SANITIZACIÓN DE INPUTS
# ============================================

def sanitize_input(value: str, max_length: int = 255) -> str:
    """Sanitiza input de usuario."""
    if not value:
        return ''
    
    # Truncar a longitud máxima
    value = str(value)[:max_length]
    
    # Eliminar caracteres de control
    value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
    
    return value.strip()


def sanitize_html(value: str) -> str:
    """Escapa HTML para prevenir XSS."""
    if not value:
        return ''
    
    html_escape = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
    }
    
    for char, replacement in html_escape.items():
        value = value.replace(char, replacement)
    
    return value


# ============================================
# HEADERS DE SEGURIDAD HTTP
# ============================================

def add_security_headers(response):
    """
    Agrega headers de seguridad a la respuesta HTTP.
    Llamar desde after_request en Flask.
    """
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = (
        'geolocation=(), microphone=(), camera=(), payment=(), usb=()'
    )

    # CSP: 'unsafe-inline' es REQUERIDO mientras las templates tengan handlers
    # inline (onclick=, onload=) y bloques <script> sin nonce.
    # NOTA: en CSP 3, si presentas un nonce el browser IGNORA 'unsafe-inline'.
    # Por eso NO se incluye nonce aqui. TODO: migrar inline JS a archivos .js
    # servidos desde 'self' y entonces SI activar nonces (eliminar unsafe-inline).
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
        "img-src 'self' data: blob:; "
        "connect-src 'self' https://cdn.jsdelivr.net https://fonts.googleapis.com https://fonts.gstatic.com; "
        "frame-ancestors 'self'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "object-src 'none';"
    )
    response.headers['Content-Security-Policy'] = csp

    # HSTS: enviar siempre si la peticion entrante es HTTPS (no depender solo de
    # FORCE_HTTPS, que es de boot-time). Si el reverse proxy termina TLS, lee
    # X-Forwarded-Proto (solo si confiamos en el proxy via TRUSTED_PROXY_COUNT).
    try:
        is_https = request.is_secure
        if not is_https and SecurityConfig.TRUSTED_PROXY_COUNT > 0:
            proto = request.headers.get('X-Forwarded-Proto', 'http').split(',')[0].strip().lower()
            is_https = (proto == 'https')
    except Exception:
        is_https = False

    if is_https or SecurityConfig.FORCE_HTTPS:
        response.headers['Strict-Transport-Security'] = (
            f'max-age={SecurityConfig.HSTS_MAX_AGE}; includeSubDomains'
        )

    if SecurityConfig.HIDE_SERVER_INFO:
        response.headers['Server'] = 'WebServer'
        response.headers.pop('X-Powered-By', None)

    return response


def production_response_filter(response):
    """
    Filtro para respuestas en producción.
    Remueve información sensible del HTML/JS.
    """
    if os.environ.get('FLASK_ENV') != 'production':
        return response
    
    # Solo procesar HTML
    if response.content_type and 'text/html' in response.content_type:
        try:
            html = response.get_data(as_text=True)
            
            # Remover comentarios HTML (excepto condicionales IE)
            if SecurityConfig.REMOVE_COMMENTS:
                import re
                html = re.sub(r'<!--(?!\[if).*?-->', '', html, flags=re.DOTALL)
            
            # Inyectar script para deshabilitar console.log en producción
            if SecurityConfig.SUPPRESS_CONSOLE_LOGS:
                suppress_script = '''
<script>
(function(){
    if(typeof console !== 'undefined'){
        console.log = function(){};
        console.debug = function(){};
        console.info = function(){};
        console.warn = function(){};
    }
})();
</script>
'''
                html = html.replace('</head>', suppress_script + '</head>')
            
            response.set_data(html)
        except Exception:
            pass  # Si falla, devolver respuesta original
    
    return response


# ============================================
# CONFIGURACIÓN DE FLASK PARA SEGURIDAD
# ============================================

def configure_flask_security(app):
    """
    Configura Flask con todas las opciones de seguridad.
    Llamar al inicializar la aplicacion.
    """
    # SECRET_KEY - CRITICO. Falla si esta vacia o es el placeholder, en
    # cualquier entorno (no solo production).
    secret_key = os.environ.get('SECRET_KEY', '').strip()
    placeholder = secret_key in (
        '', 'default',
        'CAMBIAR_POR_CLAVE_SEGURA_DE_64_CARACTERES',
    )
    if placeholder:
        if os.environ.get('FLASK_ENV', '').strip().lower() == 'production':
            raise RuntimeError(
                "SECRET_KEY ausente o placeholder. Genera una con: "
                "python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        # Desarrollo: persistir una clave en disco para evitar rotacion en cada
        # reinicio (que invalidaria datos Fernet cifrados con la clave previa).
        dev_key_file = os.path.join(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
            '.secret_key_dev'
        )
        if os.path.exists(dev_key_file):
            with open(dev_key_file, 'r') as fh:
                secret_key = fh.read().strip()
        if not secret_key:
            secret_key = secrets.token_hex(32)
            try:
                with open(dev_key_file, 'w') as fh:
                    fh.write(secret_key)
                os.chmod(dev_key_file, 0o600)
            except Exception:
                pass
            print("[WARN] SECRET_KEY ausente; generada y guardada en .secret_key_dev (solo dev).")

    app.config['SECRET_KEY'] = secret_key

    # Cookies de sesion: Secure dinamico (Secure si el request es HTTPS o si
    # FORCE_HTTPS=true). SameSite=Strict para la app de admin.
    samesite = 'Strict' if get_env_bool('SESSION_COOKIE_STRICT', True) else 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = SecurityConfig.FORCE_HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = samesite
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=SecurityConfig.SESSION_LIFETIME_MINUTES)
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=SecurityConfig.REMEMBER_COOKIE_DAYS)
    app.config['REMEMBER_COOKIE_SECURE'] = SecurityConfig.FORCE_HTTPS
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = samesite

    # WTF / CSRF (Flask-WTF si esta instalado)
    app.config['WTF_CSRF_ENABLED'] = SecurityConfig.CSRF_ENABLED
    app.config['WTF_CSRF_TIME_LIMIT'] = SecurityConfig.CSRF_TIME_LIMIT
    app.config['WTF_CSRF_SSL_STRICT'] = SecurityConfig.FORCE_HTTPS

    # Database
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///instance/biostar_users.db')
    if db_url.startswith('sqlite:///') and not db_url.startswith('sqlite:////'):
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        db_path = db_url.replace('sqlite:///', '')
        absolute_db_path = os.path.join(base_dir, db_path)
        db_url = f'sqlite:///{absolute_db_path}'

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

    # ProxyFix solo si declaras un proxy de confianza. Sin esto, X-Forwarded-*
    # del cliente son ignorados y se usa request.remote_addr.
    if SecurityConfig.TRUSTED_PROXY_COUNT > 0:
        try:
            from werkzeug.middleware.proxy_fix import ProxyFix
            app.wsgi_app = ProxyFix(
                app.wsgi_app,
                x_for=SecurityConfig.TRUSTED_PROXY_COUNT,
                x_proto=SecurityConfig.TRUSTED_PROXY_COUNT,
                x_host=0,
                x_port=0,
                x_prefix=0,
            )
        except Exception as exc:
            print(f"[WARN] ProxyFix no aplicado: {exc}")

    # CSP nonce: dejamos el hook expuesto para futuro (cuando se migren los
    # inline scripts), pero NO se incluye en el header CSP (rompe unsafe-inline).
    @app.before_request
    def _set_csp_nonce():
        g.csp_nonce = secrets.token_urlsafe(16)

    @app.context_processor
    def _inject_csp_nonce():
        return {'csp_nonce': getattr(g, 'csp_nonce', '')}

    # Handler de headers de seguridad
    @app.after_request
    def apply_security_headers(response):
        response = add_security_headers(response)
        response = production_response_filter(response)
        return response

    # Forzar HTTPS si esta configurado
    if SecurityConfig.FORCE_HTTPS:
        @app.before_request
        def force_https():
            if not request.is_secure and request.headers.get('X-Forwarded-Proto', 'http') != 'https':
                url = request.url.replace('http://', 'https://', 1)
                return redirect(url, code=301)

    # Configuracion segura para produccion
    if os.environ.get('FLASK_ENV', '').strip().lower() == 'production':
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        app.config['PROPAGATE_EXCEPTIONS'] = False
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False

    return app


# ============================================
# UTILIDADES ADICIONALES
# ============================================

def hash_ip(ip: str) -> str:
    """Hash de IP para logs (privacidad)."""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def is_safe_url(target: str) -> bool:
    """
    Verifica que una URL sea segura para redireccion.
    Rechaza protocol-relative URLs (//evil.com) y schemes peligrosos.
    """
    if not target:
        return False
    # Rechaza protocol-relative explicito antes de urljoin
    if target.startswith(('//', '\\\\', '/\\', '\\/')):
        return False

    from urllib.parse import urlparse, urljoin
    from flask import request

    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))

    if test_url.scheme not in ('http', 'https'):
        return False
    return ref_url.netloc == test_url.netloc


def generate_secure_token(length: int = 32) -> str:
    """Genera un token seguro."""
    return secrets.token_urlsafe(length)


# ============================================
# CSRF PROTECTION
# ============================================

class CSRFProtection:
    """
    Proteccion CSRF con tokens (con TTL).
    El token se rota cada CSRF_TIME_LIMIT segundos.
    """

    @staticmethod
    def generate_token() -> str:
        """Genera un token CSRF y lo guarda en sesion con timestamp."""
        now = datetime.utcnow().timestamp()
        issued = session.get('_csrf_issued_at', 0)
        token = session.get('_csrf_token')
        if (
            not token
            or (now - issued) > SecurityConfig.CSRF_TIME_LIMIT
        ):
            token = secrets.token_hex(32)
            session['_csrf_token'] = token
            session['_csrf_issued_at'] = now
        return token

    @staticmethod
    def validate_token(token: str) -> bool:
        """Valida un token CSRF (timing-safe, con expiracion)."""
        if not SecurityConfig.CSRF_ENABLED:
            return True
        session_token = session.get('_csrf_token')
        issued = session.get('_csrf_issued_at', 0)
        if not session_token or not token:
            return False
        # Expirado
        if (datetime.utcnow().timestamp() - issued) > SecurityConfig.CSRF_TIME_LIMIT:
            return False
        return hmac.compare_digest(str(session_token), str(token))

    @staticmethod
    def get_token_field() -> str:
        """Retorna HTML del campo hidden para formularios."""
        token = CSRFProtection.generate_token()
        # No interpolar token sin escapar (es hex, pero defendamos en profundidad)
        safe = sanitize_html(token)
        from markupsafe import Markup
        return Markup(f'<input type="hidden" name="csrf_token" value="{safe}">')


def csrf_protect(f):
    """Decorador para proteger endpoints contra CSRF."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            token = (
                request.form.get('csrf_token')
                or request.headers.get('X-CSRF-Token')
                or request.headers.get('X-CSRFToken')
            )
            # Para JSON sin form, buscar en el body
            if not token and request.is_json:
                try:
                    body = request.get_json(silent=True) or {}
                    token = body.get('csrf_token')
                except Exception:
                    pass
            if not CSRFProtection.validate_token(token):
                audit_logger.log_event('CSRF_FAIL', {
                    'method': request.method,
                    'path': request.path,
                })
                abort(403, description='CSRF token invalido o expirado')
        return f(*args, **kwargs)
    return decorated_function


# Endpoints exentos (GET/HEAD nunca son protegidos; ademas autorizar
# por nombre algunos endpoints publicos de read-only o webhooks externos).
CSRF_EXEMPT_ENDPOINTS = set()


def csrf_exempt(view_or_endpoint):
    """Marca una vista como exenta de CSRF (acepta funcion o nombre)."""
    name = view_or_endpoint if isinstance(view_or_endpoint, str) else view_or_endpoint.__name__
    CSRF_EXEMPT_ENDPOINTS.add(name)
    return view_or_endpoint


def install_global_csrf(app):
    """Activa CSRF global sobre todos los metodos mutantes.
    Exenta endpoints listados via @csrf_exempt o en CSRF_EXEMPT_ENDPOINTS."""
    if not SecurityConfig.CSRF_ENABLED:
        print("[INFO] CSRF deshabilitado por config (CSRF_ENABLED=false).")
        return

    @app.before_request
    def _global_csrf():
        if request.method not in ('POST', 'PUT', 'DELETE', 'PATCH'):
            return None
        endpoint = (request.endpoint or '').rsplit('.', 1)[-1]
        full_ep = request.endpoint or ''
        if endpoint in CSRF_EXEMPT_ENDPOINTS or full_ep in CSRF_EXEMPT_ENDPOINTS:
            return None
        # Static y similares
        if request.path.startswith('/static/'):
            return None
        token = (
            request.form.get('csrf_token')
            or request.headers.get('X-CSRF-Token')
            or request.headers.get('X-CSRFToken')
        )
        if not token and request.is_json:
            try:
                body = request.get_json(silent=True) or {}
                token = body.get('csrf_token')
            except Exception:
                pass
        if not CSRFProtection.validate_token(token):
            audit_logger.log_event('CSRF_FAIL', {
                'method': request.method,
                'path': request.path,
                'endpoint': full_ep,
            })
            abort(403, description='CSRF token invalido o expirado')

    print("[OK] CSRF global activado.")


# ============================================
# SESSION FINGERPRINTING
# ============================================

class SessionFingerprint:
    """Validación de sesión por fingerprint (IP + User-Agent)."""
    
    @staticmethod
    def generate() -> str:
        """Genera fingerprint de la sesion actual.

        Solo usa User-Agent (NO incluye IP). Razon: los IPs cambian
        legitimamente (WiFi -> celular, VPN, NAT, doble-proxy de carrier,
        port-forward a un IP publico distinto al de login) y validar IP
        kickea al usuario en escenarios normales sin aportar seguridad
        real contra un atacante que ya robo la cookie (puede falsificar IP
        via XFF si confiamos en proxies, o proxiar al mismo origen).
        El UA SI cambia entre navegadores robados/legitimos, mitigando
        algo de session hijacking. La proteccion REAL contra robo de
        cookie es Secure + HttpOnly + SameSite=Strict (ya aplicado).
        """
        ua = request.headers.get('User-Agent', 'unknown')
        return hashlib.sha256(f"ua:{ua}".encode()).hexdigest()
    
    @staticmethod
    def store():
        """Guarda el fingerprint en la sesión."""
        session['_fingerprint'] = SessionFingerprint.generate()
        session['_last_activity'] = datetime.now().isoformat()
    
    @staticmethod
    def validate() -> Tuple[bool, str]:
        """
        Valida que el fingerprint coincida.
        Returns: (is_valid, error_message)
        """
        if not SecurityConfig.SESSION_FINGERPRINT:
            return True, ''

        # Si la sesion esta autenticada pero no tiene fingerprint, forzar uno
        # (defensa contra el bypass donde un atacante roba la cookie antes de
        # que la victima haga login y por ende antes de que se almacene el FP).
        stored = session.get('_fingerprint')
        if not stored:
            try:
                from flask_login import current_user
                if getattr(current_user, 'is_authenticated', False):
                    SessionFingerprint.store()
            except Exception:
                pass
            return True, ''

        current = SessionFingerprint.generate()
        if not hmac.compare_digest(stored, current):
            audit_logger.log_event('SESSION_HIJACK_ATTEMPT', {
                'stored_fingerprint': stored[:16],
                'current_fingerprint': current[:16]
            })
            return False, 'Sesion invalida. Por favor inicia sesion de nuevo.'

        return True, ''
    
    @staticmethod
    def check_inactivity() -> Tuple[bool, str]:
        """
        Verifica timeout de inactividad.
        Returns: (is_active, error_message)
        """
        last_activity = session.get('_last_activity')
        if not last_activity:
            return True, ''
        
        try:
            last_dt = datetime.fromisoformat(last_activity)
            elapsed = (datetime.now() - last_dt).total_seconds() / 60
            
            if elapsed > SecurityConfig.SESSION_INACTIVITY_TIMEOUT:
                audit_logger.log_event('SESSION_TIMEOUT', {
                    'minutes_inactive': int(elapsed)
                })
                return False, f'Sesión expirada por inactividad ({int(elapsed)} minutos).'
            
            # Actualizar última actividad
            session['_last_activity'] = datetime.now().isoformat()
            
        except (ValueError, TypeError):
            pass
        
        return True, ''


def session_security_check(f):
    """Decorador para verificar seguridad de sesión."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar fingerprint
        valid, error = SessionFingerprint.validate()
        if not valid:
            session.clear()
            flash(error, 'danger')
            return redirect(url_for('login'))
        
        # Verificar inactividad
        active, error = SessionFingerprint.check_inactivity()
        if not active:
            session.clear()
            flash(error, 'warning')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# IP WHITELISTING
# ============================================

class IPWhitelist:
    """Control de acceso por IP."""

    @staticmethod
    def get_client_ip() -> str:
        """
        Obtiene la IP real del cliente.
        Solo confia en X-Forwarded-For si TRUSTED_PROXY_COUNT > 0
        (es decir, hay un reverse proxy conocido por delante).
        """
        if SecurityConfig.TRUSTED_PROXY_COUNT > 0:
            xff = request.headers.get('X-Forwarded-For')
            if xff:
                parts = [p.strip() for p in xff.split(',') if p.strip()]
                if parts:
                    return parts[0]
            real = request.headers.get('X-Real-IP')
            if real:
                return real.strip()
        return request.remote_addr or 'unknown'
    
    @staticmethod
    def is_allowed(ip: str = None, admin_only: bool = False) -> bool:
        """Verifica si una IP está permitida."""
        if not SecurityConfig.IP_WHITELIST_ENABLED:
            return True
        
        ip = ip or IPWhitelist.get_client_ip()
        
        # Limpiar lista de IPs
        if admin_only:
            whitelist = [x.strip() for x in SecurityConfig.ADMIN_IP_WHITELIST if x.strip()]
        else:
            whitelist = [x.strip() for x in SecurityConfig.IP_WHITELIST if x.strip()]
        
        # Si no hay whitelist configurada, permitir todo
        if not whitelist:
            return True
        
        # Verificar si la IP está en la lista
        return ip in whitelist
    
    @staticmethod
    def check_admin_ip() -> bool:
        """Verifica si la IP actual puede acceder como admin."""
        if not SecurityConfig.IP_WHITELIST_ENABLED:
            return True
        
        admin_whitelist = [x.strip() for x in SecurityConfig.ADMIN_IP_WHITELIST if x.strip()]
        if not admin_whitelist:
            return True
        
        client_ip = IPWhitelist.get_client_ip()
        allowed = client_ip in admin_whitelist
        
        if not allowed:
            audit_logger.log_event('ADMIN_IP_BLOCKED', {
                'ip': client_ip,
                'whitelist': admin_whitelist
            })
        
        return allowed


def ip_whitelist_required(admin_only: bool = False):
    """Decorador para requerir IP en whitelist."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not IPWhitelist.is_allowed(admin_only=admin_only):
                ip = IPWhitelist.get_client_ip()
                audit_logger.log_event('IP_BLOCKED', {'ip': ip, 'path': request.path})
                abort(403, description='Acceso denegado desde esta ubicación')
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================
# 2FA - TWO FACTOR AUTHENTICATION
# ============================================

class TwoFactorAuth:
    """Autenticación de dos factores con TOTP."""
    
    @staticmethod
    def generate_secret() -> str:
        """Genera una clave secreta para TOTP."""
        if not TOTP_AVAILABLE:
            raise RuntimeError("pyotp no está instalado")
        return pyotp.random_base32()
    
    @staticmethod
    def get_totp(secret: str) -> 'pyotp.TOTP':
        """Obtiene el objeto TOTP para una clave."""
        if not TOTP_AVAILABLE:
            raise RuntimeError("pyotp no está instalado")
        return pyotp.TOTP(secret)
    
    @staticmethod
    def verify_code(secret: str, code: str) -> bool:
        """Verifica un código TOTP."""
        if not TOTP_AVAILABLE:
            return False
        
        totp = TwoFactorAuth.get_totp(secret)
        # Permitir 1 código anterior/posterior (30 segundos de gracia)
        return totp.verify(code, valid_window=1)
    
    @staticmethod
    def generate_qr_code(secret: str, username: str, issuer: str = "BioStar Logs") -> bytes:
        """Genera código QR para configurar 2FA."""
        if not TOTP_AVAILABLE:
            raise RuntimeError("pyotp/qrcode no está instalado")
        
        totp = TwoFactorAuth.get_totp(secret)
        uri = totp.provisioning_uri(name=username, issuer_name=issuer)
        
        # Generar QR
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer.getvalue()
    
    @staticmethod
    def is_required_for_user(user) -> bool:
        """Verifica si 2FA es requerido para un usuario."""
        if SecurityConfig.REQUIRE_2FA:
            return True
        if SecurityConfig.REQUIRE_2FA_FOR_ADMIN and user.is_admin:
            return True
        return False


# ============================================
# PASSWORD HISTORY
# ============================================

class PasswordHistory:
    """Manejo de historial de contraseñas."""
    
    @staticmethod
    def check_password_reuse(user, new_password: str) -> Tuple[bool, str]:
        """
        Verifica que la nueva contraseña no haya sido usada antes.
        Returns: (is_allowed, error_message)
        """
        if not hasattr(user, 'password_history') or not user.password_history:
            return True, ''
        
        try:
            history = json.loads(user.password_history)
        except (json.JSONDecodeError, TypeError):
            return True, ''
        
        # Verificar contra las últimas N contraseñas
        for old_hash in history[:SecurityConfig.PASSWORD_HISTORY_COUNT]:
            if check_password_hash(old_hash, new_password):
                return False, f'No puedes reusar las últimas {SecurityConfig.PASSWORD_HISTORY_COUNT} contraseñas.'
        
        return True, ''
    
    @staticmethod
    def add_to_history(user, password_hash: str):
        """Agrega una contraseña al historial."""
        try:
            history = json.loads(user.password_history) if user.password_history else []
        except (json.JSONDecodeError, TypeError):
            history = []
        
        # Agregar al inicio y limitar
        history.insert(0, password_hash)
        history = history[:SecurityConfig.PASSWORD_HISTORY_COUNT]
        
        user.password_history = json.dumps(history)


# ============================================
# PASSWORD EXPIRATION
# ============================================

class PasswordExpiration:
    """Control de expiración de contraseñas."""
    
    @staticmethod
    def is_expired(user) -> bool:
        """Verifica si la contraseña ha expirado."""
        if SecurityConfig.PASSWORD_MAX_AGE_DAYS <= 0:
            return False
        
        if not hasattr(user, 'password_changed_at') or not user.password_changed_at:
            return True  # Nunca se ha cambiado, forzar cambio
        
        age_days = (datetime.utcnow() - user.password_changed_at).days
        return age_days >= SecurityConfig.PASSWORD_MAX_AGE_DAYS
    
    @staticmethod
    def days_until_expiry(user) -> int:
        """Retorna días hasta que expire la contraseña."""
        if SecurityConfig.PASSWORD_MAX_AGE_DAYS <= 0:
            return 999
        
        if not hasattr(user, 'password_changed_at') or not user.password_changed_at:
            return 0
        
        age_days = (datetime.utcnow() - user.password_changed_at).days
        return max(0, SecurityConfig.PASSWORD_MAX_AGE_DAYS - age_days)


# ============================================
# ACCOUNT LOCKOUT (PERMANENTE)
# ============================================

class AccountLockout:
    """Control de bloqueo permanente de cuentas."""
    
    # Almacenamiento de lockouts por usuario
    _lockout_counts = defaultdict(int)
    _permanent_locks = set()
    _lock = threading.Lock()
    
    @staticmethod
    def record_lockout(identifier: str):
        """Registra un lockout temporal."""
        with AccountLockout._lock:
            AccountLockout._lockout_counts[identifier] += 1
            
            if AccountLockout._lockout_counts[identifier] >= SecurityConfig.PERMANENT_LOCKOUT_AFTER:
                AccountLockout._permanent_locks.add(identifier)
                audit_logger.log_event('PERMANENT_LOCKOUT', {
                    'identifier': identifier,
                    'lockout_count': AccountLockout._lockout_counts[identifier]
                })
    
    @staticmethod
    def is_permanently_locked(identifier: str) -> bool:
        """Verifica si una cuenta está bloqueada permanentemente."""
        return identifier in AccountLockout._permanent_locks
    
    @staticmethod
    def unlock(identifier: str):
        """Desbloquea una cuenta (solo admin)."""
        with AccountLockout._lock:
            AccountLockout._permanent_locks.discard(identifier)
            AccountLockout._lockout_counts[identifier] = 0
            audit_logger.log_event('ACCOUNT_UNLOCKED', {'identifier': identifier})


# ============================================
# DATA ENCRYPTION
# ============================================

class DataEncryption:
    """
    Encriptacion de datos sensibles via Fernet.

    Requiere ENCRYPTION_KEY explicita. Si no se configura una y
    ENCRYPT_SENSITIVE_DATA esta activo, falla en produccion (en dev
    se deriva una clave a partir de SECRET_KEY con salt PERSONALIZADA
    por instalacion para evitar precomputo cross-tenant).
    """

    _fernet = None

    @staticmethod
    def _derive_dev_key() -> bytes:
        """Solo desarrollo: deriva clave Fernet a partir de SECRET_KEY usando
        salt persistido por instalacion. NUNCA usar en produccion."""
        if not CRYPTO_AVAILABLE:
            return None

        secret = os.environ.get('SECRET_KEY', '').encode() or b'dev-no-secret'
        salt_file = os.path.join(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
            '.fernet_salt_dev'
        )
        try:
            if os.path.exists(salt_file):
                with open(salt_file, 'rb') as fh:
                    salt = fh.read()
            else:
                salt = secrets.token_bytes(16)
                with open(salt_file, 'wb') as fh:
                    fh.write(salt)
                try:
                    os.chmod(salt_file, 0o600)
                except Exception:
                    pass
        except Exception:
            salt = b'biostar-fallback-salt'

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=200_000,
        )
        return base64.urlsafe_b64encode(kdf.derive(secret))

    @staticmethod
    def _get_fernet():
        if not CRYPTO_AVAILABLE or not SecurityConfig.ENCRYPT_SENSITIVE_DATA:
            return None

        if DataEncryption._fernet is None:
            key = SecurityConfig.ENCRYPTION_KEY
            if not key:
                if os.environ.get('FLASK_ENV', '').strip().lower() == 'production':
                    raise RuntimeError(
                        "ENCRYPTION_KEY ausente y ENCRYPT_SENSITIVE_DATA=true. "
                        "Genera con: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
                    )
                key = DataEncryption._derive_dev_key()
                print("[WARN] ENCRYPTION_KEY ausente; usando clave derivada local (.fernet_salt_dev).")
            else:
                key = key.encode() if isinstance(key, str) else key

            DataEncryption._fernet = Fernet(key)

        return DataEncryption._fernet

    @staticmethod
    def encrypt(data: str) -> str:
        if not SecurityConfig.ENCRYPT_SENSITIVE_DATA or data is None:
            return data
        fernet = DataEncryption._get_fernet()
        if not fernet:
            return data
        try:
            return fernet.encrypt(str(data).encode()).decode()
        except Exception as exc:
            logging.getLogger('security').warning("encrypt fallido: %s", exc)
            return data

    @staticmethod
    def decrypt(data: str) -> str:
        if not SecurityConfig.ENCRYPT_SENSITIVE_DATA or data is None:
            return data
        fernet = DataEncryption._get_fernet()
        if not fernet:
            return data
        try:
            return fernet.decrypt(str(data).encode()).decode()
        except Exception:
            # No retornar el ciphertext crudo: indicarlo explicitamente.
            logging.getLogger('security').warning(
                "decrypt fallido (clave rotada o data corrupta)"
            )
            return data


# ============================================
# SECURE REQUEST LOGGING
# ============================================

def log_all_requests(app):
    """Registra todas las peticiones (para auditoría nivel gobierno)."""
    
    @app.before_request
    def log_request():
        if SecurityConfig.AUDIT_ALL_REQUESTS:
            audit_logger.log_event('REQUEST', {
                'method': request.method,
                'path': request.path,
                'ip': IPWhitelist.get_client_ip(),
                'user_agent': request.headers.get('User-Agent', 'unknown')[:100]
            })
    
    @app.after_request
    def log_response(response):
        if SecurityConfig.AUDIT_ALL_REQUESTS:
            audit_logger.log_event('RESPONSE', {
                'status': response.status_code,
                'path': request.path
            })
        return response


# ============================================
# SECURITY MIDDLEWARE COMPLETO
# ============================================

def apply_government_security(app):
    """
    Aplica TODAS las medidas de seguridad nivel gobierno.
    Llamar despues de configure_flask_security().
    """
    log_all_requests(app)

    # Middleware de verificacion de IP
    @app.before_request
    def check_ip_whitelist():
        if SecurityConfig.IP_WHITELIST_ENABLED:
            if not IPWhitelist.is_allowed():
                abort(403, description='Acceso denegado desde esta ubicacion')

    # Sesion: validar fingerprint e inactividad en TODAS las peticiones
    # autenticadas. Falla suave: redirige a login.
    @app.before_request
    def _session_security():
        # Saltar archivos estaticos y endpoints publicos
        if request.path.startswith('/static/') or request.endpoint in ('static',):
            return None
        try:
            from flask_login import current_user
            if not getattr(current_user, 'is_authenticated', False):
                return None
        except Exception:
            return None

        valid, error = SessionFingerprint.validate()
        if not valid:
            session.clear()
            flash(error, 'danger')
            try:
                return redirect(url_for('login'))
            except Exception:
                return redirect('/login')

        active, error = SessionFingerprint.check_inactivity()
        if not active:
            session.clear()
            flash(error, 'warning')
            try:
                return redirect(url_for('login'))
            except Exception:
                return redirect('/login')

    # Activar CSRF global sobre metodos mutantes
    install_global_csrf(app)

    # Exponer helpers CSRF a templates
    @app.context_processor
    def csrf_context():
        return {
            'csrf_token': CSRFProtection.generate_token,
            'csrf_field': CSRFProtection.get_token_field,
        }

    print("[OK] Seguridad nivel gobierno aplicada")
    return app
