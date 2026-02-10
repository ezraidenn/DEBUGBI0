"""
Main Flask application for BioStar Debug Monitor.
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytz

from webapp.models import (
    db, User, DeviceCategory, DeviceConfig, UserDevicePermission, 
    init_db, get_or_create_device_config,
    MobPerUser, PresetUsuario, IncidenciaDia
)
from webapp.realtime_monitor import RealtimeMonitor
from webapp.realtime_sse import RealtimeSSE, create_sse_response
from webapp.cache_manager import init_cache, cache_manager, cached
from webapp.monitoring import init_monitoring, monitor_error, monitor_event
from webapp.pagination import paginate_list
from src.api.device_monitor import DeviceMonitor, EVENT_CODES
from src.utils.config import Config

try:
    from flask_compress import Compress
    COMPRESS_AVAILABLE = True
except ImportError:
    COMPRESS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Timezone configuration
MEXICO_TZ = pytz.timezone('America/Mexico_City')  # UTC-6

# Helper function para convertir UTC a hora local de México
def utc_to_local(dt):
    """Convierte datetime UTC a hora local de México (UTC-6)."""
    if dt is None:
        return None
    
    # Si es string, convertir a datetime
    if isinstance(dt, str):
        try:
            from dateutil import parser
            dt = parser.parse(dt)
        except:
            return None
    
    # Si no es datetime, retornar None
    if not isinstance(dt, datetime):
        return None
    
    # Si ya tiene timezone info
    if dt.tzinfo is not None:
        return dt.astimezone(MEXICO_TZ)
    
    # Si no tiene timezone, asumimos que es UTC
    utc_dt = pytz.utc.localize(dt)
    return utc_dt.astimezone(MEXICO_TZ)

# Helper function para formatear datetime a string local
def format_local_time(dt, format_str='%H:%M:%S'):
    """Formatea datetime a string en hora local de México."""
    if dt is None:
        return 'N/A'
    
    local_dt = utc_to_local(dt)
    return local_dt.strftime(format_str)

# Helper function para filtrar eventos por horario
def filter_events_by_time(events, start_hour=5, start_minute=30, end_hour=23, end_minute=59):
    """
    Filtra eventos para EXCLUIR los que ocurren entre 00:00 y 05:29 AM.
    Solo muestra eventos entre 5:30 AM y 11:59 PM (hora local de México) del DÍA ACTUAL.
    """
    filtered_events = []
    
    # Obtener fecha actual en hora local
    today_local = datetime.now(MEXICO_TZ).date()
    
    for event in events:
        event_dt = event.get('datetime')
        if event_dt is None:
            continue
        
        # Si es string, convertir a datetime
        if isinstance(event_dt, str):
            try:
                from dateutil import parser
                event_dt = parser.parse(event_dt)
            except:
                continue
        
        # Si no es datetime, saltar
        if not isinstance(event_dt, datetime):
            continue
        
        # Convertir a hora local
        try:
            local_dt = utc_to_local(event_dt)
        except:
            continue
        
        # Verificar que sea del día actual
        if local_dt.date() != today_local:
            continue
        
        # Obtener hora y minuto
        event_hour = local_dt.hour
        event_minute = local_dt.minute
        
        # Verificar si está dentro del rango
        # Convertir a minutos desde medianoche para comparación más fácil
        event_time_minutes = event_hour * 60 + event_minute
        start_time_minutes = start_hour * 60 + start_minute
        end_time_minutes = end_hour * 60 + end_minute
        
        if start_time_minutes <= event_time_minutes <= end_time_minutes:
            filtered_events.append(event)
    
    return filtered_events

# Helper function para clasificar eventos
def classify_event(event_code):
    """Clasifica un evento según su código."""
    if event_code in EVENT_CODES['ACCESS_GRANTED']:
        return 'success', 'Acceso Concedido'
    elif event_code in EVENT_CODES['ACCESS_DENIED']:
        return 'danger', 'Acceso Denegado'
    elif event_code in EVENT_CODES['FORCED_OPEN']:
        return 'warning', 'Puerta Forzada'
    elif event_code in EVENT_CODES['DOOR_LOCKED']:
        return 'info', 'Puerta Bloqueada'
    elif event_code in EVENT_CODES['DOOR_OPEN']:
        return 'primary', 'Puerta Abierta'
    elif event_code in EVENT_CODES['DOOR_CLOSE']:
        return 'secondary', 'Puerta Cerrada'
    else:
        return 'secondary', 'Otro Evento'

# Initialize Flask app
app = Flask(__name__)

# ============================================
# CONFIGURACIÓN DE SEGURIDAD NIVEL GOBIERNO
# ============================================
from webapp.security import (
    # Configuración base
    configure_flask_security,
    apply_government_security,
    CSRFProtection,
    SecurityConfig,
    audit_logger,
    
    # Rate Limiting
    check_login_rate_limit,
    record_login_success,
    record_login_failure,
    rate_limit_api,
    
    # Validación
    validate_password,
    get_password_policy_text,
    sanitize_input,
    
    # CSRF
    CSRFProtection,
    csrf_protect,
    
    # Session Security
    SessionFingerprint,
    session_security_check,
    
    # IP Whitelisting
    IPWhitelist,
    ip_whitelist_required,
    
    # 2FA
    TwoFactorAuth,
    TOTP_AVAILABLE,
    
    # Account Security
    AccountLockout,
    PasswordExpiration,
)

# Aplicar configuración de seguridad base
configure_flask_security(app)
logger.info("✓ Configuración de seguridad base aplicada")

# Aplicar seguridad nivel gobierno
apply_government_security(app)
logger.info("✓ Seguridad nivel gobierno aplicada")

# Cache configuration
app.config['REDIS_URL'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
app.config['CACHE_ENABLED'] = os.environ.get('CACHE_ENABLED', 'true').lower() == 'true'

# Initialize compression for better performance
if COMPRESS_AVAILABLE:
    compress = Compress()
    compress.init_app(app)
    app.config['COMPRESS_MIMETYPES'] = [
        'text/html', 'text/css', 'text/xml', 'application/json',
        'application/javascript', 'text/javascript'
    ]
    app.config['COMPRESS_LEVEL'] = 6
    app.config['COMPRESS_MIN_SIZE'] = 500
    logger.info("✓ Compresión HTTP habilitada")

# Initialize SocketIO for real-time updates (restringir origins en producción)
allowed_origins = "*" if os.environ.get('FLASK_ENV') != 'production' else None
socketio = SocketIO(app, cors_allowed_origins=allowed_origins, async_mode='threading')

# Initialize database
init_db(app)

# Initialize cache system
try:
    init_cache(app, redis_url=app.config['REDIS_URL'], enabled=app.config['CACHE_ENABLED'])
    logger.info("✓ Sistema de caché inicializado")
except Exception as e:
    logger.warning(f"⚠ No se pudo inicializar caché: {e}")

# Initialize monitoring and health checks
try:
    init_monitoring(app)
    logger.info("✓ Sistema de monitoreo inicializado")
except Exception as e:
    logger.warning(f"⚠ No se pudo inicializar monitoreo: {e}")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

# Register helper functions for Jinja templates
app.jinja_env.globals.update(classify_event=classify_event)
app.jinja_env.globals.update(csrf_token=CSRFProtection.generate_token)

# Initialize BioStar config
biostar_config = Config()

def get_monitor():
    """Get or create monitor instance for current request."""
    monitor = DeviceMonitor(biostar_config)
    if not monitor.login():
        return None
    return monitor


# Initialize real-time monitor
realtime_monitor = RealtimeMonitor(socketio, get_monitor)
realtime_monitor.start()


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.query.get(int(user_id))


# ==================== WEBSOCKET EVENTS ====================

@socketio.on('connect', namespace='/realtime')
def handle_connect():
    """Cliente conectado vía WebSocket."""
    print(f"✓ Cliente conectado: {request.sid}")
    emit('connected', {'message': 'Conectado al servidor en tiempo real'})


@socketio.on('disconnect', namespace='/realtime')
def handle_disconnect():
    """Cliente desconectado."""
    print(f"✗ Cliente desconectado: {request.sid}")


@socketio.on('monitor_device', namespace='/realtime')
def handle_monitor_device(data):
    """Cliente solicita monitorear un dispositivo."""
    device_id = data.get('device_id')
    if device_id:
        realtime_monitor.add_device(device_id)
        join_room(f'device_{device_id}')
        emit('monitoring', {'device_id': device_id, 'status': 'active'})
        print(f"📍 Cliente {request.sid} monitoreando dispositivo {device_id}")


@socketio.on('stop_monitor_device', namespace='/realtime')
def handle_stop_monitor(data):
    """Cliente deja de monitorear un dispositivo."""
    device_id = data.get('device_id')
    if device_id:
        realtime_monitor.remove_device(device_id)
        leave_room(f'device_{device_id}')
        emit('monitoring', {'device_id': device_id, 'status': 'inactive'})
        print(f"📍 Cliente {request.sid} dejó de monitorear dispositivo {device_id}")


# ==================== AUTHENTICATION ROUTES ====================

@app.route('/')
def index():
    """Home page - redirect to dashboard if logged in."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page con protección NIVEL GOBIERNO."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', ''), max_length=50)
        password = request.form.get('password', '')
        totp_code = request.form.get('totp_code', '')
        remember = request.form.get('remember', False)
        
        # Rate limiting por IP y usuario
        client_ip = IPWhitelist.get_client_ip()
        rate_key = f"{client_ip}:{username}"
        
        # Verificar bloqueo permanente
        if AccountLockout.is_permanently_locked(username):
            audit_logger.log_event('LOGIN_PERMANENT_BLOCK', {'user': username}, client_ip)
            flash('Esta cuenta ha sido bloqueada permanentemente. Contacta al administrador.', 'danger')
            return render_template('login.html')
        
        # Verificar rate limit
        allowed, error_msg = check_login_rate_limit(rate_key)
        if not allowed:
            # Registrar lockout para posible bloqueo permanente
            AccountLockout.record_lockout(username)
            flash(error_msg, 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Verificar si cuenta está bloqueada en DB
            if user.is_locked():
                flash('Tu cuenta está bloqueada temporalmente. Intenta más tarde.', 'danger')
                audit_logger.log_event('LOGIN_LOCKED', {'user': username}, client_ip)
                return redirect(url_for('login'))
            
            if not user.is_active:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
                audit_logger.log_event('LOGIN_INACTIVE', {'user': username}, client_ip)
                return redirect(url_for('login'))
            
            # Verificar 2FA si está habilitado
            if user.totp_enabled and TOTP_AVAILABLE:
                if not totp_code:
                    # Mostrar formulario de 2FA
                    session['pending_2fa_user'] = user.id
                    return render_template('login.html', require_2fa=True, username=username)
                
                if not TwoFactorAuth.verify_code(user.totp_secret, totp_code):
                    audit_logger.log_event('2FA_FAIL', {'user': username}, client_ip)
                    flash('Código de verificación incorrecto.', 'danger')
                    return render_template('login.html', require_2fa=True, username=username)
            
            # Login exitoso
            login_user(user, remember=remember)
            user.update_last_login()
            user.reset_failed_attempts()
            record_login_success(rate_key)
            
            # Guardar fingerprint de sesión
            SessionFingerprint.store()
            
            # Verificar si debe cambiar contraseña
            if user.must_change_password or user.is_password_expired(SecurityConfig.PASSWORD_MAX_AGE_DAYS):
                flash('Tu contraseña ha expirado. Debes cambiarla.', 'warning')
                return redirect(url_for('change_password'))
            
            # Verificar redirección segura
            next_page = request.args.get('next')
            if next_page and not next_page.startswith('/'):
                next_page = None  # Prevenir open redirect
            
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            # Login fallido
            if user:
                user.record_failed_login()
                # Bloquear temporalmente si excede intentos
                if user.failed_login_attempts >= SecurityConfig.LOGIN_MAX_ATTEMPTS:
                    user.lock_temporarily(SecurityConfig.LOGIN_LOCKOUT_MINUTES)
                    audit_logger.log_event('ACCOUNT_LOCKED', {
                        'user': username,
                        'attempts': user.failed_login_attempts
                    }, client_ip)
            
            record_login_failure(rate_key)
            flash('Usuario o contraseña incorrectos.', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout user."""
    username = current_user.username
    logout_user()
    session.clear()  # Limpiar toda la sesión
    audit_logger.log_event('LOGOUT', {'user': username})
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('login'))


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Cambio de contraseña obligatorio."""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Verificar contraseña actual
        if not current_user.check_password(current_password):
            flash('Contraseña actual incorrecta.', 'danger')
            return render_template('change_password.html')
        
        # Verificar que las nuevas coincidan
        if new_password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('change_password.html')
        
        # Validar política de contraseñas
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            flash(error_msg, 'danger')
            return render_template('change_password.html')
        
        # Verificar que no sea reutilizada
        if current_user.check_password_reuse(new_password):
            flash(f'No puedes reusar las últimas {SecurityConfig.PASSWORD_HISTORY_COUNT} contraseñas.', 'danger')
            return render_template('change_password.html')
        
        # Cambiar contraseña
        current_user.set_password(new_password)
        db.session.commit()
        
        audit_logger.log_event('PASSWORD_CHANGE', {'user': current_user.username})
        flash('Contraseña cambiada exitosamente.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('change_password.html', 
                          password_policy=get_password_policy_text())


# ==================== API ENDPOINTS ====================

@app.route('/api/unique-users')
@login_required
def get_unique_users():
    """Obtiene todos los usuarios únicos del día con su último chequeo."""
    monitor = get_monitor()
    if not monitor:
        return jsonify({'error': 'No monitor'}), 500
    
    # Obtener dispositivos según permisos del usuario
    all_devices = monitor.get_all_devices(refresh=False)
    
    if current_user.is_admin or current_user.can_see_all_events:
        devices = all_devices
    else:
        allowed_ids = current_user.get_allowed_device_ids()
        if allowed_ids is not None:
            allowed_ids_str = [str(d) for d in allowed_ids]
            devices = [d for d in all_devices if str(d['id']) in allowed_ids_str]
        else:
            devices = all_devices
    
    # Recolectar usuarios únicos con su último chequeo
    users_dict = {}  # user_id -> {name, last_check, device_name}
    
    for device in devices:
        events = monitor.get_device_events_today(device['id'])
        events = monitor._filter_events_by_time(events)
        
        for event in events:
            # Solo accesos concedidos (usar EVENT_CODES del device_monitor)
            event_code = event.get('event_type_id', {}).get('code', '')
            if event_code not in EVENT_CODES['ACCESS_GRANTED']:
                continue
            
            # Extraer user_id
            user_data = event.get('user_id', {})
            if isinstance(user_data, dict):
                user_id = user_data.get('user_id') or user_data.get('id')
                user_name = user_data.get('name', '')
            else:
                user_id = user_data
                user_name = ''
            
            if not user_id or str(user_id) in ['', 'None', 'nan']:
                continue
            
            user_id_str = str(user_id)
            event_time = event.get('datetime', '')
            device_name = event.get('device_id', {}).get('name', device.get('name', ''))
            
            # Guardar o actualizar si es más reciente
            if user_id_str not in users_dict:
                users_dict[user_id_str] = {
                    'user_id': user_id_str,
                    'name': user_name,
                    'last_check': event_time,
                    'device': device_name
                }
            else:
                # Comparar timestamps para quedarse con el más reciente
                if event_time > users_dict[user_id_str]['last_check']:
                    users_dict[user_id_str]['last_check'] = event_time
                    users_dict[user_id_str]['device'] = device_name
                    if user_name:  # Actualizar nombre si está disponible
                        users_dict[user_id_str]['name'] = user_name
    
    # Convertir a lista ordenada por último chequeo (más reciente primero)
    users_list = sorted(users_dict.values(), key=lambda x: x['last_check'], reverse=True)
    
    return jsonify({
        'success': True,
        'total': len(users_list),
        'users': users_list
    })


@app.route('/api/buscar-usuarios')
@login_required
def buscar_usuarios_api():
    """Endpoint simple para buscar usuarios del día por nombre o ID."""
    query = request.args.get('q', '').strip().lower()
    
    if not query or len(query) < 2:
        return jsonify({'success': True, 'users': [], 'message': 'Query muy corta'})
    
    monitor = get_monitor()
    if not monitor:
        return jsonify({'success': False, 'message': 'Monitor no disponible'}), 500
    
    # Obtener dispositivos
    all_devices = monitor.get_all_devices(refresh=False)
    
    # Recolectar usuarios únicos
    users_dict = {}
    
    for device in all_devices:
        try:
            events = monitor.get_device_events_today(device['id'])
            events = monitor._filter_events_by_time(events)
            
            for event in events:
                event_code = event.get('event_type_id', {}).get('code', '')
                if event_code not in EVENT_CODES['ACCESS_GRANTED']:
                    continue
                
                user_data = event.get('user_id', {})
                if isinstance(user_data, dict):
                    user_id = user_data.get('user_id') or user_data.get('id')
                    user_name = user_data.get('name', '')
                else:
                    user_id = user_data
                    user_name = ''
                
                if not user_id or str(user_id) in ['', 'None', 'nan']:
                    continue
                
                user_id_str = str(user_id)
                
                if user_id_str not in users_dict:
                    users_dict[user_id_str] = {
                        'user_id': user_id_str,
                        'name': user_name or f'Usuario {user_id_str}'
                    }
                elif user_name and not users_dict[user_id_str].get('name'):
                    users_dict[user_id_str]['name'] = user_name
        except Exception as e:
            continue
    
    # Filtrar por query
    results = []
    for user in users_dict.values():
        name_lower = (user.get('name') or '').lower()
        id_lower = str(user.get('user_id', '')).lower()
        
        if query in name_lower or query in id_lower:
            results.append(user)
            if len(results) >= 30:
                break
    
    # Ordenar por nombre
    results.sort(key=lambda x: (x.get('name') or '').lower())
    
    return jsonify({
        'success': True,
        'users': results,
        'total': len(results)
    })


# ==================== DASHBOARD ROUTES ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - CARGA RÁPIDA con datos via AJAX."""
    # Renderizar inmediatamente con datos mínimos
    # Los datos reales se cargan via /api/dashboard-data
    return render_template('dashboard.html', 
                           devices_by_type={}, 
                           total_granted=0,
                           total_users=0,
                           total_devices=0,
                           lazy_load=True)  # Flag para carga lazy


@app.route('/api/dashboard-data')
@login_required
def api_dashboard_data():
    """API para cargar datos del dashboard de forma asíncrona."""
    try:
        monitor = get_monitor()
        if not monitor:
            logger.warning("BioStar no disponible - retornando dashboard vacío")
            return jsonify({
                'success': True,
                'devices': [],
                'total_granted': 0,
                'total_users': 0,
                'total_devices': 0,
                'warning': 'BioStar no disponible. Verifica la conexión al servidor.'
            })
        
        # Get all devices (usar caché)
        all_devices = monitor.get_all_devices(refresh=False)
        
        if not all_devices:
            return jsonify({
                'success': True,
                'devices': [],
                'total_granted': 0,
                'total_users': 0,
                'total_devices': 0
            })
        
        # Get device configurations
        device_configs = {}
        try:
            for config in DeviceConfig.query.all():
                device_configs[config.device_id] = config
                device_configs[str(config.device_id)] = config
        except Exception as e:
            logger.error(f"Error cargando configuraciones de dispositivos: {e}")
        
        # Filtrar según permisos
        if current_user.is_admin or current_user.can_see_all_events:
            devices = all_devices
        else:
            allowed_ids = current_user.get_allowed_device_ids()
            if allowed_ids is not None:
                allowed_ids_str = set(str(d) for d in allowed_ids)
                devices = [d for d in all_devices if str(d.get('id', '')) in allowed_ids_str]
            else:
                devices = all_devices
        
        # Carga paralela de resúmenes
        def fetch_device_summary(device):
            try:
                summary, user_ids = monitor.get_debug_summary_with_users(device['id'])
                summary['total_events'] = summary.get('access_granted', 0)
                return device['id'], summary, user_ids
            except Exception as e:
                logger.error(f"Error obteniendo resumen del dispositivo {device.get('id')}: {e}")
                return device.get('id'), {'access_granted': 0, 'unique_users': 0, 'total_events': 0}, set()
        
        total_granted = 0
        all_user_ids = set()
        device_summaries = {}
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(fetch_device_summary, d): d for d in devices}
            for future in as_completed(futures):
                try:
                    device_id, summary, user_ids = future.result()
                    device_summaries[device_id] = (summary, user_ids)
                except Exception as e:
                    logger.error(f"Error procesando future: {e}")
                    continue
        
        # Procesar resultados
        devices_data = []
        for device in devices:
            try:
                summary, user_ids = device_summaries.get(device.get('id'), ({}, set()))
                total_granted += summary.get('access_granted', 0)
                all_user_ids.update(user_ids)
                
                config = device_configs.get(device.get('id')) or device_configs.get(str(device.get('id')))
                device_type = config.device_type if config else 'checador'
                
                devices_data.append({
                    'id': device.get('id'),
                    'name': device.get('name', 'Sin nombre'),
                    'alias': config.alias if config else None,
                    'device_type': device_type,
                    'summary': summary
                })
            except Exception as e:
                logger.error(f"Error procesando dispositivo {device.get('id')}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'devices': devices_data,
            'total_granted': total_granted,
            'total_users': len(all_user_ids),
            'total_devices': len(devices)
        })
    
    except Exception as e:
        logger.error(f"Error crítico en api_dashboard_data: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f'Error interno del servidor: {str(e)}'}), 500


@app.route('/debug/general')
@login_required
def debug_general():
    """General debug view - all devices."""
    monitor = get_monitor()
    if not monitor:
        flash('Error al conectar con BioStar.', 'danger')
        return redirect(url_for('dashboard'))
    
    devices = monitor.get_all_devices(refresh=True)
    
    # Get summary for all devices
    all_summaries = []
    for device in devices:
        summary = monitor.get_debug_summary(device['id'])
        all_summaries.append({
            'device': device,
            'summary': summary
        })
    
    return render_template('debug_general.html', summaries=all_summaries)


@app.route('/debug/device/<int:device_id>')
@login_required
def debug_device(device_id):
    """Individual device debug view."""
    monitor = get_monitor()
    if not monitor:
        flash('Error al conectar con BioStar.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get device config
    device_config = DeviceConfig.query.filter_by(device_id=device_id).first()
    
    # Get all devices first to populate cache
    all_devices = monitor.get_all_devices(refresh=True)
    
    # Get device info
    device = monitor.get_device_by_id(device_id)
    
    if not device:
        flash(f'Dispositivo {device_id} no encontrado.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get events and filter by time (5:30 AM - 11:59 PM)
    events = monitor.get_device_events_today(device_id)
    events = filter_events_by_time(events)
    
    # FILTER: Only show ACCESS GRANTED events
    ACCESS_GRANTED_CODES = [
        '4097', '4098', '4099', '4100', '4101', '4102', '4103', '4104', '4105', '4106', '4107',
        '4112', '4113', '4114', '4115', '4118', '4119', '4120', '4121', '4122', '4123', '4128', '4129',
        '4865', '4866', '4867', '4868', '4869', '4870', '4871', '4872'
    ]
    
    def get_event_code(event):
        """Extract event code from event_type_id (can be dict or direct value)."""
        event_type = event.get('event_type_id')
        if isinstance(event_type, dict):
            return event_type.get('code')
        return str(event_type) if event_type else None
    
    granted_events = [e for e in events if get_event_code(e) in ACCESS_GRANTED_CODES]
    
    # Calculate first and last event BEFORE converting to local
    first_event_dt = None
    last_event_dt = None
    if granted_events:
        for event in granted_events:
            event_dt = event.get('datetime')
            if event_dt:
                if isinstance(event_dt, str):
                    from dateutil import parser
                    event_dt = parser.parse(event_dt)
                
                if not first_event_dt or event_dt < first_event_dt:
                    first_event_dt = event_dt
                if not last_event_dt or event_dt > last_event_dt:
                    last_event_dt = event_dt
    
    # Convert to dataframe (this properly extracts nested fields)
    df = monitor.events_to_dataframe(granted_events)
    
    # Convert datetime to local time for display
    if not df.empty and 'datetime' in df.columns:
        df['datetime'] = df['datetime'].apply(lambda x: utc_to_local(x) if x else None)
    
    # Convert to list of dicts for template
    events_list = df.to_dict('records') if not df.empty else []
    
    # Calculate PAIRS logic (for checadores)
    # Es checador si: no tiene config (default) O si está configurado como checador
    is_checador = (not device_config) or (device_config.device_type == 'checador')
    
    # Inicializar pairs_data siempre para checadores
    pairs_data = {
        'complete': [],
        'pending': [],
        'multiple': []
    } if is_checador else None
    
    if is_checador and events_list:
        # Group events by user
        user_events = {}
        for event in events_list:
            # Extraer user_id correctamente (puede ser dict o string)
            user_id_raw = event.get('user_id')
            if isinstance(user_id_raw, dict):
                user_id = user_id_raw.get('user_id') or user_id_raw.get('id')
                user_name = user_id_raw.get('name') or event.get('user_name') or 'Desconocido'
            else:
                user_id = user_id_raw
                user_name = event.get('user_name') or 'Desconocido'
            
            # Convertir a string y validar
            user_id = str(user_id) if user_id else None
            
            if user_id and user_id not in ['', 'None', 'nan', 'NaN']:
                if user_id not in user_events:
                    user_events[user_id] = {
                        'user_name': user_name,
                        'events': []
                    }
                user_events[user_id]['events'].append(event)
        
        # Classify users into pairs_data
        for user_id, data in user_events.items():
            count = len(data['events'])
            first_event = min(data['events'], key=lambda x: x['datetime'] if x.get('datetime') else datetime.min)
            
            user_info = {
                'user_id': user_id,
                'user_name': data['user_name'],
                'event_count': count,
                'first_event': first_event['datetime']
            }
            
            if count == 2:
                last_event = max(data['events'], key=lambda x: x['datetime'] if x.get('datetime') else datetime.min)
                user_info['last_event'] = last_event['datetime']
                pairs_data['complete'].append(user_info)
            elif count == 1:
                pairs_data['pending'].append(user_info)
            else:
                pairs_data['multiple'].append(user_info)
    
    # Get summary - usar user_events que ya tiene los user_ids correctamente extraídos
    # Si es checador, usar el conteo de user_events que ya procesó correctamente
    if is_checador and pairs_data:
        unique_users_count = len(pairs_data['pending']) + len(pairs_data['complete']) + len(pairs_data['multiple'])
    else:
        # Fallback: extraer user_id correctamente
        unique_users = set()
        for e in events_list:
            uid_raw = e.get('user_id')
            if isinstance(uid_raw, dict):
                uid = uid_raw.get('user_id') or uid_raw.get('id')
            else:
                uid = uid_raw
            uid = str(uid) if uid else None
            if uid and uid not in ['', 'None', 'nan', 'NaN']:
                unique_users.add(uid)
        unique_users_count = len(unique_users)
    
    # CORRECCIÓN CRÍTICA: Usar granted_events original, no events_list
    # events_list puede tener más eventos debido al procesamiento del DataFrame
    summary = {
        'total_events': len(granted_events),
        'access_granted': len(granted_events),
        'access_denied': 0,
        'unique_users': unique_users_count,
        'first_event': utc_to_local(first_event_dt) if first_event_dt else None,
        'last_event': utc_to_local(last_event_dt) if last_event_dt else None
    }
    
    return render_template('debug_device.html', 
                         device=device, 
                         device_config=device_config,
                         events=events_list, 
                         summary=summary,
                         pairs_data=pairs_data,
                         is_checador=is_checador)


@app.route('/debug/device/<int:device_id>/export')
@login_required
def export_device_debug(device_id):
    """Export device debug to Excel."""
    monitor = get_monitor()
    if not monitor:
        return jsonify({'error': 'Error al conectar con BioStar'}), 500
    
    try:
        filename = monitor.export_daily_debug(device_id)
        return jsonify({
            'success': True,
            'filename': filename,
            'message': 'Debug exportado exitosamente'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/debug/device/<int:device_id>/clear-cache', methods=['POST'])
@login_required
def clear_device_cache(device_id):
    """Clear cache and reload all data for a device."""
    try:
        # Get monitor instance
        monitor = get_monitor()
        if not monitor:
            return jsonify({'error': 'Error al conectar con BioStar'}), 500
        
        # Clear any cached data (if your monitor has cache)
        # Force re-authentication
        monitor.client.session_id = None
        monitor.client.session_expires = None
        
        # Re-authenticate
        if not monitor.client.login():
            return jsonify({'error': 'Error al reautenticar con BioStar'}), 500
        
        # Get fresh data
        events = monitor.get_device_events_today(device_id)
        
        return jsonify({
            'success': True,
            'message': f'Cache limpiado. {len(events)} eventos recargados.',
            'events_count': len(events)
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/clear-all-cache', methods=['POST'])
@login_required
def clear_all_cache():
    """Clear cache and reload all data for dashboard."""
    try:
        # Get monitor instance
        monitor = get_monitor()
        if not monitor:
            return jsonify({'error': 'Error al conectar con BioStar'}), 500
        
        # Clear any cached data
        # Force re-authentication
        monitor.client.session_id = None
        monitor.client.session_expires = None
        
        # Re-authenticate
        if not monitor.client.login():
            return jsonify({'error': 'Error al reautenticar con BioStar'}), 500
        
        # Get fresh device list
        devices = monitor.get_all_devices()
        
        return jsonify({
            'success': True,
            'message': f'Cache limpiado. {len(devices)} dispositivos recargados.',
            'devices_count': len(devices)
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== STAT CARD DETAILS API ====================

@app.route('/api/device/<int:device_id>/stat/<stat_type>')
@login_required
def get_stat_details(device_id, stat_type):
    """Get detailed information for a specific stat card."""
    monitor = get_monitor()
    if not monitor:
        return jsonify({'error': 'Error al conectar con BioStar'}), 500
    
    try:
        # Get device info
        device = monitor.get_device_by_id(device_id)
        if not device:
            return jsonify({'error': 'Dispositivo no encontrado'}), 404
        
        # Get all events for today and filter by time (5:30 AM - 11:59 PM)
        events = monitor.get_device_events_today(device_id)
        events = filter_events_by_time(events)
        
        if stat_type == 'total':
            # Total events with timestamps
            event_list = []
            for e in events[-50:]:  # Last 50 events
                user_id = e.get('user_id')
                # Convertir user_id a string si es necesario
                if isinstance(user_id, dict):
                    user_id = str(user_id.get('id', 'N/A'))
                elif user_id is None:
                    user_id = 'N/A'
                else:
                    user_id = str(user_id)
                
                event_code = e.get('event_code')
                if event_code is None:
                    event_code = 'N/A'
                else:
                    event_code = str(event_code)
                
                event_list.append({
                    'datetime': format_local_time(e.get('datetime')),
                    'user': user_id,
                    'event_type': classify_event(event_code)[1],
                    'event_code': event_code
                })
            
            return jsonify({
                'title': 'Total de Eventos',
                'subtitle': f'{device.get("alias") or device.get("name")}',
                'count': len(events),
                'data': event_list[::-1]  # Reverse to show newest first
            })
        
        elif stat_type == 'granted':
            # Access granted events
            granted_events = [e for e in events if e.get('event_code') in EVENT_CODES['ACCESS_GRANTED']]
            event_list = []
            for e in granted_events[-50:]:
                user_id = e.get('user_id')
                if isinstance(user_id, dict):
                    user_id = str(user_id.get('id', 'N/A'))
                elif user_id is None:
                    user_id = 'N/A'
                else:
                    user_id = str(user_id)
                
                event_list.append({
                    'datetime': format_local_time(e.get('datetime')),
                    'user': user_id,
                    'door': e.get('door_name', 'N/A')
                })
            
            return jsonify({
                'title': 'Accesos Concedidos',
                'subtitle': f'{device.get("alias") or device.get("name")}',
                'count': len(granted_events),
                'data': event_list[::-1]
            })
        
        elif stat_type == 'denied':
            # Access denied events
            denied_events = [e for e in events if e.get('event_code') in EVENT_CODES['ACCESS_DENIED']]
            event_list = []
            for e in denied_events[-50:]:
                user_id = e.get('user_id')
                if isinstance(user_id, dict):
                    user_id = str(user_id.get('id', 'N/A'))
                elif user_id is None:
                    user_id = 'N/A'
                else:
                    user_id = str(user_id)
                
                event_code = e.get('event_code', '0')
                event_list.append({
                    'datetime': format_local_time(e.get('datetime')),
                    'user': user_id,
                    'reason': classify_event(str(event_code))[1]
                })
            
            return jsonify({
                'title': 'Accesos Denegados',
                'subtitle': f'{device.get("alias") or device.get("name")}',
                'count': len(denied_events),
                'data': event_list[::-1]
            })
        
        elif stat_type == 'users':
            # Unique users
            user_ids = set()
            user_events = {}
            
            for e in events:
                user_id_obj = e.get('user_id')
                
                # Extraer información del usuario
                if isinstance(user_id_obj, dict):
                    user_id_num = user_id_obj.get('user_id')
                    user_name = user_id_obj.get('name')  # El nombre está DENTRO del dict
                else:
                    user_id_num = user_id_obj
                    user_name = None
                
                # Determinar la clave única para agrupar
                # Prioridad: user_name > user_id
                if user_name and user_name != 'N/A' and user_name != '-':
                    # Usar nombre como clave
                    unique_key = user_name
                    display_name = user_name
                elif user_id_num and user_id_num != 'N/A' and user_id_num != '-':
                    # Usar ID como clave
                    unique_key = str(user_id_num)
                    display_name = str(user_id_num)
                else:
                    continue  # Saltar eventos sin usuario identificable
                
                user_ids.add(unique_key)
                if unique_key not in user_events:
                    user_events[unique_key] = {
                        'user_id': unique_key,
                        'user_name': display_name,
                        'total_events': 0,
                        'granted': 0,
                        'denied': 0,
                        'last_access': None
                    }
                
                user_events[unique_key]['total_events'] += 1
                
                event_code = e.get('event_code')
                if event_code in EVENT_CODES['ACCESS_GRANTED']:
                    user_events[unique_key]['granted'] += 1
                elif event_code in EVENT_CODES['ACCESS_DENIED']:
                    user_events[unique_key]['denied'] += 1
                
                event_time = e.get('datetime')
                if event_time:
                    if not user_events[unique_key]['last_access'] or event_time > user_events[unique_key]['last_access']:
                        user_events[unique_key]['last_access'] = event_time
            
            # Format user data
            user_list = []
            for user_data in user_events.values():
                last_access = format_local_time(user_data['last_access'])
                
                user_list.append({
                    'user_id': user_data['user_name'],  # Mostrar nombre en lugar de ID
                    'total_events': user_data['total_events'],
                    'granted': user_data['granted'],
                    'denied': user_data['denied'],
                    'last_access': last_access
                })
            
            # Sort by total events
            user_list.sort(key=lambda x: x['total_events'], reverse=True)
            
            return jsonify({
                'title': 'Usuarios Únicos',
                'subtitle': f'{device.get("alias") or device.get("name")}',
                'count': len(user_ids),
                'data': user_list[:50]  # Top 50 users
            })
        
        else:
            return jsonify({'error': 'Tipo de estadística no válido'}), 400
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== USER MANAGEMENT ROUTES (ADMIN ONLY) ====================

@app.route('/users')
@login_required
def users_list():
    """List all users (admin only)."""
    if not current_user.is_admin:
        flash('No tienes permisos para acceder a esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('users.html', users=users)


@app.route('/users/create', methods=['GET', 'POST'])
@login_required
def user_create():
    """Create new user (admin only)."""
    if not current_user.is_admin:
        flash('No tienes permisos para acceder a esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Sanitizar inputs
        username = sanitize_input(request.form.get('username', ''), max_length=50)
        email = sanitize_input(request.form.get('email', ''), max_length=120)
        password = request.form.get('password', '')
        full_name = sanitize_input(request.form.get('full_name', ''), max_length=100)
        is_admin = request.form.get('is_admin') == 'on'
        is_auditor = request.form.get('is_auditor') == 'on'
        can_see_all_events = request.form.get('can_see_all_events') == 'on'
        can_manage_devices = request.form.get('can_manage_devices') == 'on'
        
        # Validar contraseña con política de seguridad
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            flash(error_msg, 'danger')
            return redirect(url_for('user_create'))
        
        # Validate username
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe.', 'danger')
            return redirect(url_for('user_create'))
        
        if User.query.filter_by(email=email).first():
            flash('El email ya está registrado.', 'danger')
            return redirect(url_for('user_create'))
        
        # Create user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            is_admin=is_admin,
            is_auditor=is_auditor,
            can_see_all_events=can_see_all_events,
            can_manage_devices=can_manage_devices
        )
        user.set_password(password)
        
        # Auditoría
        audit_logger.log_event('USER_CREATE', {
            'user': current_user.username,
            'created_user': username,
            'is_admin': is_admin
        })
        
        db.session.add(user)
        db.session.commit()
        
        # Assign devices
        device_ids = request.form.getlist('devices')
        for device_id in device_ids:
            permission = UserDevicePermission(
                user_id=user.id,
                device_id=int(device_id),
                can_view=True,
                can_export=True
            )
            db.session.add(permission)
        db.session.commit()
        
        flash(f'Usuario {username} creado exitosamente.', 'success')
        return redirect(url_for('users_list'))
    
    # Get devices for assignment
    monitor = get_monitor()
    devices = []
    if monitor:
        devices = monitor.get_all_devices() or []
        # Enrich with local config and convert IDs to int
        for device in devices:
            if 'id' in device:
                device['id'] = int(device['id'])
            config = DeviceConfig.query.filter_by(device_id=device.get('id')).first()
            if config and config.alias:
                device['alias'] = config.alias
    
    return render_template('user_form.html', user=None, action='create', 
                           devices=devices, assigned_devices=[])


@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(user_id):
    """Edit user (admin only)."""
    if not current_user.is_admin:
        flash('No tienes permisos para acceder a esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Sanitizar inputs
        user.username = sanitize_input(request.form.get('username', ''), max_length=50)
        user.email = sanitize_input(request.form.get('email', ''), max_length=120)
        user.full_name = sanitize_input(request.form.get('full_name', ''), max_length=100)
        user.is_admin = request.form.get('is_admin') == 'on'
        user.is_auditor = request.form.get('is_auditor') == 'on'
        user.is_active = request.form.get('is_active') == 'on'
        user.can_see_all_events = request.form.get('can_see_all_events') == 'on'
        user.can_manage_devices = request.form.get('can_manage_devices') == 'on'
        
        # Update password if provided (con validación)
        password = request.form.get('password', '')
        if password:
            is_valid, error_msg = validate_password(password)
            if not is_valid:
                flash(error_msg, 'danger')
                return redirect(url_for('user_edit', user_id=user_id))
            user.set_password(password)
        
        # Auditoría
        audit_logger.log_event('USER_EDIT', {
            'user': current_user.username,
            'edited_user': user.username,
            'is_admin': user.is_admin,
            'is_active': user.is_active
        })
        
        # Update device permissions
        # First, remove all existing permissions
        UserDevicePermission.query.filter_by(user_id=user.id).delete()
        
        # Then add new ones
        device_ids = request.form.getlist('devices')
        for device_id in device_ids:
            permission = UserDevicePermission(
                user_id=user.id,
                device_id=int(device_id),
                can_view=True,
                can_export=True
            )
            db.session.add(permission)
        
        db.session.commit()
        flash(f'Usuario {user.username} actualizado exitosamente.', 'success')
        return redirect(url_for('users_list'))
    
    # Get devices for assignment
    monitor = get_monitor()
    devices = []
    if monitor:
        devices = monitor.get_all_devices() or []
        # Enrich with local config
        for device in devices:
            config = DeviceConfig.query.filter_by(device_id=device.get('id')).first()
            if config and config.alias:
                device['alias'] = config.alias
    
    # Get assigned device IDs (as integers)
    assigned_devices = [p.device_id for p in user.device_permissions.all()]
    
    # Convert device IDs to int for comparison in template
    for device in devices:
        if 'id' in device:
            device['id'] = int(device['id'])
    
    return render_template('user_form.html', user=user, action='edit',
                           devices=devices, assigned_devices=assigned_devices)


@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def user_delete(user_id):
    """Delete user (admin only)."""
    if not current_user.is_admin:
        audit_logger.log_event('USER_DELETE_DENIED', {
            'user': current_user.username,
            'target_user_id': user_id
        })
        return jsonify({'error': 'No autorizado'}), 403
    
    if user_id == current_user.id:
        return jsonify({'error': 'No puedes eliminar tu propio usuario'}), 400
    
    user = User.query.get_or_404(user_id)
    deleted_username = user.username
    
    # Auditoría ANTES de eliminar
    audit_logger.log_event('USER_DELETE', {
        'user': current_user.username,
        'deleted_user': deleted_username
    })
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Usuario {deleted_username} eliminado'})


# ==================== REALTIME SSE ROUTES ====================

@app.route('/stream/device/<int:device_id>')
@login_required
def stream_device_events(device_id):
    """
    Stream SSE de eventos en tiempo real para un dispositivo específico.
    Más eficiente que WebSockets para streaming unidireccional.
    """
    monitor = get_monitor()
    if not monitor:
        return jsonify({'error': 'Error al conectar con BioStar'}), 500
    
    # Crear gestor SSE
    sse = RealtimeSSE(monitor)
    
    # Intervalo de polling (2 segundos por defecto)
    interval = request.args.get('interval', 2, type=int)
    interval = max(1, min(interval, 10))  # Entre 1 y 10 segundos
    
    # Retornar stream SSE
    return create_sse_response(sse.stream_device_events(device_id, interval))


@app.route('/stream/all-devices')
@login_required
def stream_all_devices():
    """
    Stream SSE de eventos en tiempo real para todos los dispositivos.
    """
    monitor = get_monitor()
    if not monitor:
        return jsonify({'error': 'Error al conectar con BioStar'}), 500
    
    # Crear gestor SSE
    sse = RealtimeSSE(monitor)
    
    # Intervalo de polling (3 segundos por defecto para todos)
    interval = request.args.get('interval', 3, type=int)
    interval = max(2, min(interval, 15))  # Entre 2 y 15 segundos
    
    # Retornar stream SSE
    return create_sse_response(sse.stream_all_devices(interval))


# ==================== API ROUTES ====================

@app.route('/api/devices')
@login_required
def api_devices():
    """API endpoint to get all devices."""
    monitor = get_monitor()
    if not monitor:
        return jsonify({'error': 'Error al conectar con BioStar'}), 500
    
    devices = monitor.get_all_devices(refresh=True)
    return jsonify(devices)


@app.route('/api/device/<int:device_id>/summary')
@login_required
def api_device_summary(device_id):
    """API endpoint to get device summary."""
    monitor = get_monitor()
    if not monitor:
        return jsonify({'error': 'Error al conectar con BioStar'}), 500
    
    summary = monitor.get_debug_summary(device_id)
    
    # Convert datetime to string
    if summary['first_event']:
        summary['first_event'] = summary['first_event'].strftime('%H:%M:%S')
    if summary['last_event']:
        summary['last_event'] = summary['last_event'].strftime('%H:%M:%S')
    
    return jsonify(summary)


@app.route('/api/device/<int:device_id>/events')
@login_required
def api_device_events(device_id):
    """API endpoint to get device events with pagination."""
    try:
        monitor = get_monitor()
        if not monitor:
            return jsonify({'error': 'Error al conectar con BioStar'}), 500
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        per_page = min(per_page, 200)  # Max 200 items per page
        
        # Get events and filter by time
        events = monitor.get_device_events_today(device_id)
        events = filter_events_by_time(events)
        
        # Convert datetime to local time
        for event in events:
            if event.get('datetime'):
                local_time = utc_to_local(event['datetime'])
                event['datetime'] = local_time.isoformat() if local_time else None
        
        # Paginate
        paginated = paginate_list(events, page=page, per_page=per_page)
        
        return jsonify(paginated)
    
    except Exception as e:
        monitor_error('api_device_events')
        return jsonify({'error': str(e)}), 500


@app.route('/api/cache/stats')
@login_required
def api_cache_stats():
    """API endpoint to get cache statistics."""
    if not current_user.is_admin:
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        cache_mgr = app.extensions.get('cache_manager')
        if cache_mgr:
            stats = cache_mgr.get_stats()
            return jsonify(stats)
        else:
            return jsonify({'error': 'Cache no disponible'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cache/clear', methods=['POST'])
@login_required
def api_cache_clear():
    """API endpoint to clear cache (admin only)."""
    if not current_user.is_admin:
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        cache_mgr = app.extensions.get('cache_manager')
        if cache_mgr:
            cache_mgr.clear_all()
            return jsonify({'success': True, 'message': 'Cache limpiado'})
        else:
            return jsonify({'error': 'Cache no disponible'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== DEVICE CONFIGURATION ROUTES ====================

@app.route('/config/devices')
@login_required
def config_devices():
    """Device configuration page (admin only)."""
    if not current_user.is_admin and not current_user.can_manage_devices:
        flash('No tienes permisos para acceder a esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get devices from BioStar
    monitor = get_monitor()
    devices = []
    if monitor:
        devices = monitor.get_all_devices() or []
    
    # Debug: ver tipo de device.id
    if devices:
        print(f"[CONFIG] Ejemplo device.id: {devices[0].get('id')} (tipo: {type(devices[0].get('id'))})")
    
    # Get local configurations - usar string como key porque device.id viene como string de la API
    device_configs = {}
    for config in DeviceConfig.query.all():
        # Guardar con ambos tipos de key para asegurar match
        device_configs[config.device_id] = config
        device_configs[str(config.device_id)] = config
        print(f"[CONFIG] Cargado: device_id={config.device_id}, type={config.device_type}")
    
    print(f"[CONFIG] Total configs cargadas: {len(DeviceConfig.query.all())}")
    
    return render_template('config_devices.html', 
                           devices=devices, 
                           device_configs=device_configs)


@app.route('/config/devices/<int:device_id>', methods=['POST'])
@login_required
def config_device_save(device_id):
    """Save device configuration."""
    if not current_user.is_admin and not current_user.can_manage_devices:
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        data = request.get_json()
        print(f"[CONFIG] Guardando dispositivo {device_id}: {data}")
        
        # Get or create config
        config = DeviceConfig.query.filter_by(device_id=device_id).first()
        if not config:
            config = DeviceConfig(device_id=device_id)
            db.session.add(config)
            print(f"[CONFIG] Creando nueva configuración para {device_id}")
        else:
            print(f"[CONFIG] Actualizando configuración existente para {device_id}")
        
        # Update fields
        config.alias = data.get('alias') or None
        config.location = data.get('location') or None
        config.device_type = data.get('device_type', 'checador')
        
        print(f"[CONFIG] Valores: alias={config.alias}, location={config.location}, type={config.device_type}")
        
        db.session.commit()
        print(f"[CONFIG] Guardado exitoso para {device_id}")
        
        return jsonify({'success': True, 'message': 'Configuración guardada'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/config/categories', methods=['POST'])
@login_required
def config_category_create():
    """Create new device category."""
    if not current_user.is_admin:
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        data = request.get_json()
        
        # Check if name exists
        if DeviceCategory.query.filter_by(name=data.get('name')).first():
            return jsonify({'error': 'Ya existe una categoría con ese nombre'}), 400
        
        category = DeviceCategory(
            name=data.get('name'),
            color=data.get('color', '#6c757d'),
            icon=data.get('icon', 'bi-hdd'),
            description=data.get('description')
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({'success': True, 'id': category.id, 'message': 'Categoría creada'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/config/categories/<int:category_id>', methods=['PUT', 'DELETE'])
@login_required
def config_category_update(category_id):
    """Update or delete device category."""
    if not current_user.is_admin:
        return jsonify({'error': 'No autorizado'}), 403
    
    category = DeviceCategory.query.get_or_404(category_id)
    
    if request.method == 'DELETE':
        if category.devices.count() > 0:
            return jsonify({'error': 'No se puede eliminar: tiene dispositivos asignados'}), 400
        
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Categoría eliminada'})
    
    # PUT - Update
    try:
        data = request.get_json()
        
        category.name = data.get('name', category.name)
        category.color = data.get('color', category.color)
        category.icon = data.get('icon', category.icon)
        category.description = data.get('description', category.description)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Categoría actualizada'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# API - MODO PÁNICO
# ============================================

@app.route('/panic-button')
@login_required
def panic_button_page():
    """Página del botón de pánico."""
    if not current_user.is_admin:
        flash('No tienes permisos para acceder a esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    monitor = get_monitor()
    devices = []
    if monitor:
        devices = monitor.get_all_devices() or []
    
    return render_template('panic_button.html', devices=devices)


@app.route('/api/panic-mode/<device_id>', methods=['POST'])
@login_required
def toggle_panic_mode(device_id):
    """Activa o desactiva el modo pánico para un dispositivo."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        from webapp.models import PanicModeStatus, PanicModeLog
        from src.api.door_control import biostar_unlock_door, biostar_lock_door
        
        data = request.json
        action = data.get('action')
        activate_alarm = data.get('activate_alarm', False)
        
        monitor = get_monitor()
        device_name = f"Dispositivo {device_id}"
        if monitor:
            devices = monitor.get_all_devices()
            for d in devices:
                if str(d.get('id')) == str(device_id):
                    device_name = d.get('name', device_name)
                    break
        
        status = PanicModeStatus.query.filter_by(device_id=str(device_id)).first()
        
        if action == 'activate':
            success, message = biostar_unlock_door(device_id, activate_alarm=activate_alarm)
            
            if success:
                if not status:
                    status = PanicModeStatus(device_id=str(device_id), device_name=device_name)
                    db.session.add(status)
                
                status.is_active = True
                status.alarm_active = activate_alarm
                status.activated_at = datetime.utcnow()
                status.activated_by_user_id = current_user.id
                
                log = PanicModeLog(
                    device_id=str(device_id),
                    device_name=device_name,
                    action='activate',
                    user_id=current_user.id,
                    username=current_user.username,
                    success=True,
                    alarm_activated=activate_alarm
                )
                db.session.add(log)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'is_active': True,
                    'alarm_active': activate_alarm,
                    'message': message
                })
            else:
                log = PanicModeLog(
                    device_id=str(device_id),
                    device_name=device_name,
                    action='activate',
                    user_id=current_user.id,
                    username=current_user.username,
                    success=False,
                    error_message=message
                )
                db.session.add(log)
                db.session.commit()
                return jsonify({'success': False, 'message': message}), 500
        
        elif action == 'deactivate':
            deactivate_alarm = status.alarm_active if status else False
            success, message = biostar_lock_door(device_id, deactivate_alarm=deactivate_alarm)
            
            if success:
                if status:
                    status.is_active = False
                    status.alarm_active = False
                    status.deactivated_at = datetime.utcnow()
                    status.deactivated_by_user_id = current_user.id
                
                log = PanicModeLog(
                    device_id=str(device_id),
                    device_name=device_name,
                    action='deactivate',
                    user_id=current_user.id,
                    username=current_user.username,
                    success=True
                )
                db.session.add(log)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'is_active': False,
                    'alarm_active': False,
                    'message': message
                })
            else:
                log = PanicModeLog(
                    device_id=str(device_id),
                    device_name=device_name,
                    action='deactivate',
                    user_id=current_user.id,
                    username=current_user.username,
                    success=False,
                    error_message=message
                )
                db.session.add(log)
                db.session.commit()
                return jsonify({'success': False, 'message': message}), 500
        
        return jsonify({'success': False, 'message': 'Acción inválida'}), 400
        
    except Exception as e:
        logger.error(f"Error en modo pánico: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/panic-mode/status', methods=['GET'])
@login_required
def get_panic_status():
    """Obtiene el estado de todos los dispositivos en modo pánico."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        from webapp.models import PanicModeStatus
        
        statuses = PanicModeStatus.query.filter_by(is_active=True).all()
        
        return jsonify({
            'success': True,
            'devices': [{
                'device_id': s.device_id,
                'device_name': s.device_name,
                'is_active': s.is_active,
                'alarm_active': s.alarm_active,
                'activated_at': s.activated_at.isoformat() if s.activated_at else None,
                'activated_by': s.activated_by.username if s.activated_by else None
            } for s in statuses]
        })
    except Exception as e:
        logger.error(f"Error obteniendo estados de pánico: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# REGISTRAR BLUEPRINT DE EMERGENCIAS
# ============================================
from webapp.emergency_routes import emergency_bp
app.register_blueprint(emergency_bp)
logger.info("✓ Sistema de emergencias registrado")

# REGISTRAR BLUEPRINT DE MOVPER
# ============================================
from webapp.mobper_routes import mobper_bp, prewarm_biostar_client
app.register_blueprint(mobper_bp)
prewarm_biostar_client()  # Pre-calentar conexión BioStar en background
logger.info("✓ Sistema MovPer registrado")


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
