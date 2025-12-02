"""
Módulo de Seguridad para BioStar Logs Monitor.
Implementa protecciones contra ataques comunes.
"""
import os
import re
import logging
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Tuple, Dict, Any
from collections import defaultdict
import threading

from flask import request, abort, jsonify, g, current_app
from werkzeug.security import generate_password_hash

# ============================================
# CONFIGURACIÓN DESDE VARIABLES DE ENTORNO
# ============================================

def get_env_bool(key: str, default: bool = False) -> bool:
    """Obtiene variable de entorno como booleano."""
    value = os.environ.get(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')

def get_env_int(key: str, default: int) -> int:
    """Obtiene variable de entorno como entero."""
    try:
        return int(os.environ.get(key, default))
    except (ValueError, TypeError):
        return default


class SecurityConfig:
    """Configuración de seguridad desde variables de entorno."""
    
    # Rate Limiting
    LOGIN_RATE_LIMIT = get_env_int('LOGIN_RATE_LIMIT', 5)
    LOGIN_MAX_ATTEMPTS = get_env_int('LOGIN_MAX_ATTEMPTS', 5)
    LOGIN_LOCKOUT_MINUTES = get_env_int('LOGIN_LOCKOUT_MINUTES', 15)
    API_RATE_LIMIT = get_env_int('API_RATE_LIMIT', 60)
    
    # Password Policy
    PASSWORD_MIN_LENGTH = get_env_int('PASSWORD_MIN_LENGTH', 8)
    PASSWORD_REQUIRE_UPPER = get_env_bool('PASSWORD_REQUIRE_UPPER', True)
    PASSWORD_REQUIRE_DIGIT = get_env_bool('PASSWORD_REQUIRE_DIGIT', True)
    PASSWORD_REQUIRE_SPECIAL = get_env_bool('PASSWORD_REQUIRE_SPECIAL', True)
    
    # Session
    SESSION_LIFETIME_MINUTES = get_env_int('SESSION_LIFETIME_MINUTES', 60)
    REMEMBER_COOKIE_DAYS = get_env_int('REMEMBER_COOKIE_DAYS', 7)
    
    # HTTPS
    FORCE_HTTPS = get_env_bool('FORCE_HTTPS', False)
    
    # Audit
    SECURITY_AUDIT_LOG = get_env_bool('SECURITY_AUDIT_LOG', True)
    AUDIT_LOG_FILE = os.environ.get('AUDIT_LOG_FILE', 'logs/security_audit.log')


# ============================================
# LOGGER DE AUDITORÍA DE SEGURIDAD
# ============================================

class SecurityAuditLogger:
    """Logger especializado para eventos de seguridad."""
    
    def __init__(self):
        self.logger = logging.getLogger('security_audit')
        self.logger.setLevel(logging.INFO)
        
        # Solo configurar si está habilitado
        if SecurityConfig.SECURITY_AUDIT_LOG:
            # Crear directorio de logs si no existe
            log_dir = os.path.dirname(SecurityConfig.AUDIT_LOG_FILE)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            # Handler de archivo
            handler = logging.FileHandler(SecurityConfig.AUDIT_LOG_FILE)
            handler.setLevel(logging.INFO)
            
            # Formato detallado para auditoría
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_event(self, event_type: str, details: Dict[str, Any], ip: str = None):
        """Registra un evento de seguridad."""
        if not SecurityConfig.SECURITY_AUDIT_LOG:
            return
        
        ip = ip or self._get_client_ip()
        user = details.get('user', 'anonymous')
        
        message = f"[{event_type}] IP={ip} USER={user}"
        for key, value in details.items():
            if key != 'user':
                message += f" {key.upper()}={value}"
        
        if 'FAIL' in event_type or 'BLOCK' in event_type:
            self.logger.warning(message)
        else:
            self.logger.info(message)
    
    def _get_client_ip(self) -> str:
        """Obtiene IP real del cliente (considera proxies)."""
        try:
            # Verificar headers de proxy
            if request.headers.get('X-Forwarded-For'):
                return request.headers.get('X-Forwarded-For').split(',')[0].strip()
            if request.headers.get('X-Real-IP'):
                return request.headers.get('X-Real-IP')
            return request.remote_addr or 'unknown'
        except:
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


def check_login_rate_limit(identifier: str) -> Tuple[bool, str]:
    """
    Verifica rate limit para login.
    Returns: (allowed, error_message)
    """
    # Verificar si está bloqueado
    blocked, remaining = login_limiter.is_blocked(identifier)
    if blocked:
        audit_logger.log_event('LOGIN_BLOCKED', {
            'identifier': identifier,
            'remaining_seconds': remaining
        })
        return False, f'Cuenta bloqueada temporalmente. Intenta en {remaining // 60 + 1} minutos.'
    
    # Registrar intento
    attempts = login_limiter.record_attempt(identifier, window_seconds=60)
    
    # Verificar si excede límite
    if attempts > SecurityConfig.LOGIN_MAX_ATTEMPTS:
        login_limiter.block(identifier, SecurityConfig.LOGIN_LOCKOUT_MINUTES)
        audit_logger.log_event('LOGIN_LOCKOUT', {
            'identifier': identifier,
            'attempts': attempts,
            'lockout_minutes': SecurityConfig.LOGIN_LOCKOUT_MINUTES
        })
        return False, f'Demasiados intentos fallidos. Cuenta bloqueada por {SecurityConfig.LOGIN_LOCKOUT_MINUTES} minutos.'
    
    return True, ''


def record_login_success(identifier: str):
    """Registra login exitoso y resetea rate limit."""
    login_limiter.reset(identifier)
    audit_logger.log_event('LOGIN_SUCCESS', {'user': identifier})


def record_login_failure(identifier: str):
    """Registra intento de login fallido."""
    attempts = login_limiter.get_attempts(identifier)
    audit_logger.log_event('LOGIN_FAIL', {
        'identifier': identifier,
        'attempts': attempts,
        'max_attempts': SecurityConfig.LOGIN_MAX_ATTEMPTS
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
    Valida que la contraseña cumpla con la política de seguridad.
    Returns: (is_valid, error_message)
    """
    errors = []
    
    # Longitud mínima
    if len(password) < SecurityConfig.PASSWORD_MIN_LENGTH:
        errors.append(f'Mínimo {SecurityConfig.PASSWORD_MIN_LENGTH} caracteres')
    
    # Mayúsculas
    if SecurityConfig.PASSWORD_REQUIRE_UPPER and not re.search(r'[A-Z]', password):
        errors.append('Al menos una mayúscula')
    
    # Números
    if SecurityConfig.PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', password):
        errors.append('Al menos un número')
    
    # Caracteres especiales
    if SecurityConfig.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password):
        errors.append('Al menos un carácter especial (!@#$%^&*...)')
    
    if errors:
        return False, 'La contraseña debe tener: ' + ', '.join(errors)
    
    return True, ''


def get_password_policy_text() -> str:
    """Retorna texto descriptivo de la política de contraseñas."""
    requirements = [f'Mínimo {SecurityConfig.PASSWORD_MIN_LENGTH} caracteres']
    
    if SecurityConfig.PASSWORD_REQUIRE_UPPER:
        requirements.append('una mayúscula')
    if SecurityConfig.PASSWORD_REQUIRE_DIGIT:
        requirements.append('un número')
    if SecurityConfig.PASSWORD_REQUIRE_SPECIAL:
        requirements.append('un carácter especial')
    
    return ', '.join(requirements)


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
    # Prevenir clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # Prevenir MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # XSS Protection (legacy pero útil)
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Permissions Policy (antes Feature-Policy)
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    # Content Security Policy (básico, ajustar según necesidades)
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com; "
        "font-src 'self' fonts.gstatic.com cdn.jsdelivr.net; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'self';"
    )
    response.headers['Content-Security-Policy'] = csp
    
    # HSTS (solo si HTTPS está habilitado)
    if SecurityConfig.FORCE_HTTPS:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response


# ============================================
# CONFIGURACIÓN DE FLASK PARA SEGURIDAD
# ============================================

def configure_flask_security(app):
    """
    Configura Flask con todas las opciones de seguridad.
    Llamar al inicializar la aplicación.
    """
    # SECRET_KEY - CRÍTICO
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key or secret_key == 'CAMBIAR_POR_CLAVE_SEGURA_DE_64_CARACTERES':
        if os.environ.get('FLASK_ENV') == 'production':
            raise ValueError(
                "⚠️ ERROR CRÍTICO: SECRET_KEY no configurada. "
                "Genera una con: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        else:
            # En desarrollo, generar una temporal (no recomendado)
            import secrets
            secret_key = secrets.token_hex(32)
            print("⚠️ ADVERTENCIA: Usando SECRET_KEY temporal. Configura una en .env para producción.")
    
    app.config['SECRET_KEY'] = secret_key
    
    # Configuración de sesiones seguras
    app.config['SESSION_COOKIE_SECURE'] = SecurityConfig.FORCE_HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=SecurityConfig.SESSION_LIFETIME_MINUTES)
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=SecurityConfig.REMEMBER_COOKIE_DAYS)
    app.config['REMEMBER_COOKIE_SECURE'] = SecurityConfig.FORCE_HTTPS
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
    
    # Database
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///biostar_users.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configuración adicional
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
    
    # Registrar handler para headers de seguridad
    @app.after_request
    def apply_security_headers(response):
        return add_security_headers(response)
    
    # Forzar HTTPS si está configurado
    if SecurityConfig.FORCE_HTTPS:
        @app.before_request
        def force_https():
            if not request.is_secure and request.headers.get('X-Forwarded-Proto', 'http') != 'https':
                url = request.url.replace('http://', 'https://', 1)
                return redirect(url, code=301)
    
    return app


# ============================================
# UTILIDADES ADICIONALES
# ============================================

def hash_ip(ip: str) -> str:
    """Hash de IP para logs (privacidad)."""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def is_safe_url(target: str) -> bool:
    """Verifica que una URL sea segura para redirección."""
    from urllib.parse import urlparse, urljoin
    from flask import request
    
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def generate_secure_token(length: int = 32) -> str:
    """Genera un token seguro."""
    import secrets
    return secrets.token_urlsafe(length)
