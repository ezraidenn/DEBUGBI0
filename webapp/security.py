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
    """Configuración de seguridad NIVEL GOBIERNO desde variables de entorno."""
    
    # ==================== RATE LIMITING ====================
    LOGIN_RATE_LIMIT = get_env_int('LOGIN_RATE_LIMIT', 5)
    LOGIN_MAX_ATTEMPTS = get_env_int('LOGIN_MAX_ATTEMPTS', 5)
    LOGIN_LOCKOUT_MINUTES = get_env_int('LOGIN_LOCKOUT_MINUTES', 15)
    API_RATE_LIMIT = get_env_int('API_RATE_LIMIT', 60)
    
    # Bloqueo permanente después de X lockouts
    PERMANENT_LOCKOUT_AFTER = get_env_int('PERMANENT_LOCKOUT_AFTER', 3)
    
    # ==================== PASSWORD POLICY ====================
    PASSWORD_MIN_LENGTH = get_env_int('PASSWORD_MIN_LENGTH', 12)  # Mínimo 12 para gobierno
    PASSWORD_REQUIRE_UPPER = get_env_bool('PASSWORD_REQUIRE_UPPER', True)
    PASSWORD_REQUIRE_LOWER = get_env_bool('PASSWORD_REQUIRE_LOWER', True)
    PASSWORD_REQUIRE_DIGIT = get_env_bool('PASSWORD_REQUIRE_DIGIT', True)
    PASSWORD_REQUIRE_SPECIAL = get_env_bool('PASSWORD_REQUIRE_SPECIAL', True)
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
    return secrets.token_urlsafe(length)


# ============================================
# CSRF PROTECTION
# ============================================

class CSRFProtection:
    """Protección CSRF con tokens."""
    
    @staticmethod
    def generate_token() -> str:
        """Genera un token CSRF y lo guarda en sesión."""
        if '_csrf_token' not in session:
            session['_csrf_token'] = secrets.token_hex(32)
        return session['_csrf_token']
    
    @staticmethod
    def validate_token(token: str) -> bool:
        """Valida un token CSRF."""
        if not SecurityConfig.CSRF_ENABLED:
            return True
        
        session_token = session.get('_csrf_token')
        if not session_token or not token:
            return False
        
        # Comparación segura contra timing attacks
        return hmac.compare_digest(session_token, token)
    
    @staticmethod
    def get_token_field() -> str:
        """Retorna HTML del campo hidden para formularios."""
        token = CSRFProtection.generate_token()
        return f'<input type="hidden" name="csrf_token" value="{token}">'


def csrf_protect(f):
    """Decorador para proteger endpoints contra CSRF."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            if not CSRFProtection.validate_token(token):
                audit_logger.log_event('CSRF_FAIL', {
                    'method': request.method,
                    'path': request.path
                })
                abort(403, description='CSRF token inválido o expirado')
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# SESSION FINGERPRINTING
# ============================================

class SessionFingerprint:
    """Validación de sesión por fingerprint (IP + User-Agent)."""
    
    @staticmethod
    def generate() -> str:
        """Genera fingerprint de la sesión actual."""
        ip = request.headers.get('X-Forwarded-For', request.remote_addr) or 'unknown'
        ua = request.headers.get('User-Agent', 'unknown')
        
        # Hash del fingerprint
        data = f"{ip}:{ua}"
        return hashlib.sha256(data.encode()).hexdigest()
    
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
        
        stored = session.get('_fingerprint')
        if not stored:
            return True, ''  # Primera vez, no hay fingerprint
        
        current = SessionFingerprint.generate()
        
        if not hmac.compare_digest(stored, current):
            audit_logger.log_event('SESSION_HIJACK_ATTEMPT', {
                'stored_fingerprint': stored[:16],
                'current_fingerprint': current[:16]
            })
            return False, 'Sesión inválida. Por favor inicia sesión de nuevo.'
        
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
        """Obtiene la IP real del cliente."""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        if request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
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
    """Encriptación de datos sensibles."""
    
    _fernet = None
    
    @staticmethod
    def _get_fernet():
        """Obtiene instancia de Fernet para encriptación."""
        if not CRYPTO_AVAILABLE:
            return None
        
        if DataEncryption._fernet is None:
            key = SecurityConfig.ENCRYPTION_KEY
            if not key:
                # Generar clave derivada del SECRET_KEY
                secret = os.environ.get('SECRET_KEY', 'default').encode()
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'biostar_logs_salt',
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(secret))
            else:
                key = key.encode() if isinstance(key, str) else key
            
            DataEncryption._fernet = Fernet(key)
        
        return DataEncryption._fernet
    
    @staticmethod
    def encrypt(data: str) -> str:
        """Encripta un string."""
        if not SecurityConfig.ENCRYPT_SENSITIVE_DATA:
            return data
        
        fernet = DataEncryption._get_fernet()
        if not fernet:
            return data
        
        try:
            encrypted = fernet.encrypt(data.encode())
            return encrypted.decode()
        except Exception:
            return data
    
    @staticmethod
    def decrypt(data: str) -> str:
        """Desencripta un string."""
        if not SecurityConfig.ENCRYPT_SENSITIVE_DATA:
            return data
        
        fernet = DataEncryption._get_fernet()
        if not fernet:
            return data
        
        try:
            decrypted = fernet.decrypt(data.encode())
            return decrypted.decode()
        except Exception:
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
    Llamar después de configure_flask_security().
    """
    # Log de todas las peticiones si está habilitado
    log_all_requests(app)
    
    # Middleware de verificación de IP
    @app.before_request
    def check_ip_whitelist():
        if SecurityConfig.IP_WHITELIST_ENABLED:
            if not IPWhitelist.is_allowed():
                abort(403, description='Acceso denegado desde esta ubicación')
    
    # Agregar token CSRF a contexto de templates
    @app.context_processor
    def csrf_context():
        return {
            'csrf_token': CSRFProtection.generate_token,
            'csrf_field': CSRFProtection.get_token_field
        }
    
    print("✓ Seguridad nivel gobierno aplicada")
    return app
