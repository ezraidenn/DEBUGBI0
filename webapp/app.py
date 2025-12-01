"""
Main Flask application for BioStar Debug Monitor.
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash
import logging
from datetime import datetime, timedelta
import pytz

from webapp.models import db, User, DeviceCategory, DeviceConfig, UserDevicePermission, init_db, get_or_create_device_config
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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///biostar_users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

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
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
                return redirect(url_for('login'))
            
            login_user(user, remember=remember)
            user.update_last_login()
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout user."""
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('login'))


# ==================== DEBUG ENDPOINT (TEMPORAL) ====================

@app.route('/api/debug-events/<int:device_id>')
@login_required
def debug_events_structure(device_id):
    """Debug: Ver estructura real de eventos de la API."""
    monitor = get_monitor()
    if not monitor:
        return jsonify({'error': 'No monitor'}), 500
    
    events = monitor.get_device_events_today(device_id)
    
    # Tomar solo los primeros 3 eventos
    sample_events = events[:3] if events else []
    
    # Extraer solo la parte de user_id para debug
    user_samples = []
    for e in sample_events:
        user_samples.append({
            'event_id': e.get('id'),
            'user_id_raw': e.get('user_id'),
            'user_id_type': type(e.get('user_id')).__name__
        })
    
    return jsonify({
        'device_id': device_id,
        'total_events': len(events),
        'user_samples': user_samples
    })


# ==================== DASHBOARD ROUTES ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - Solo muestra accesos concedidos."""
    # Get monitor instance
    monitor = get_monitor()
    if not monitor:
        flash('Error al conectar con BioStar. Verifica la configuración.', 'danger')
        return render_template('dashboard.html', devices_by_type={}, error=True)
    
    # Get all devices
    all_devices = monitor.get_all_devices(refresh=True)
    
    # Get device configurations
    device_configs = {config.device_id: config for config in DeviceConfig.query.all()}
    # También guardar con string key
    for config in DeviceConfig.query.all():
        device_configs[str(config.device_id)] = config
    
    # Filtrar dispositivos según permisos del usuario
    if current_user.is_admin or current_user.can_see_all_events:
        devices = all_devices
    else:
        # Solo dispositivos asignados al usuario
        allowed_ids = current_user.get_allowed_device_ids()
        if allowed_ids is not None:
            # Convertir a strings para comparación
            allowed_ids_str = [str(d) for d in allowed_ids]
            devices = [d for d in all_devices if str(d['id']) in allowed_ids_str]
        else:
            devices = all_devices
    
    # Agrupar por tipo y calcular resumen
    devices_by_type = {}
    total_granted = 0
    total_users = 0
    
    for device in devices:
        summary = monitor.get_debug_summary(device['id'])
        summary['total_events'] = summary['access_granted']
        device['summary'] = summary
        total_granted += summary['access_granted']
        total_users += summary['unique_users']
        
        # Obtener tipo del dispositivo
        config = device_configs.get(device['id']) or device_configs.get(str(device['id']))
        device_type = config.device_type if config else 'checador'
        device['device_type'] = device_type
        
        if device_type not in devices_by_type:
            devices_by_type[device_type] = []
        devices_by_type[device_type].append(device)
    
    # Ordenar tipos: checador primero, luego alfabético
    type_order = {'checador': 0, 'puerta': 1, 'facial': 2, 'otro': 3}
    sorted_types = sorted(devices_by_type.keys(), key=lambda x: type_order.get(x, 99))
    devices_by_type = {t: devices_by_type[t] for t in sorted_types}
    
    return render_template('dashboard.html', 
                           devices_by_type=devices_by_type, 
                           total_granted=total_granted,
                           total_users=total_users,
                           total_devices=len(devices))


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
            user_id = event.get('user_id')
            if user_id and user_id != '' and user_id is not None:
                if user_id not in user_events:
                    user_events[user_id] = {
                        'user_name': event.get('user_name') or 'Desconocido',
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
    
    # Get summary - use events_list which has processed user_ids
    unique_users = set()
    for e in events_list:
        uid = e.get('user_id')
        if uid and uid != '' and uid is not None:
            unique_users.add(uid)
    
    summary = {
        'total_events': len(events_list),
        'access_granted': len(events_list),
        'access_denied': 0,
        'unique_users': len(unique_users),
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
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        is_admin = request.form.get('is_admin') == 'on'
        can_see_all_events = request.form.get('can_see_all_events') == 'on'
        can_manage_devices = request.form.get('can_manage_devices') == 'on'
        
        # Validate
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
            can_see_all_events=can_see_all_events,
            can_manage_devices=can_manage_devices
        )
        user.set_password(password)
        
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
        # Enrich with local config
        for device in devices:
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
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.full_name = request.form.get('full_name')
        user.is_admin = request.form.get('is_admin') == 'on'
        user.is_active = request.form.get('is_active') == 'on'
        user.can_see_all_events = request.form.get('can_see_all_events') == 'on'
        user.can_manage_devices = request.form.get('can_manage_devices') == 'on'
        
        # Update password if provided
        password = request.form.get('password')
        if password:
            user.set_password(password)
        
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
    
    # Get assigned device IDs
    assigned_devices = [p.device_id for p in user.device_permissions.all()]
    
    return render_template('user_form.html', user=user, action='edit',
                           devices=devices, assigned_devices=assigned_devices)


@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def user_delete(user_id):
    """Delete user (admin only)."""
    if not current_user.is_admin:
        return jsonify({'error': 'No autorizado'}), 403
    
    if user_id == current_user.id:
        return jsonify({'error': 'No puedes eliminar tu propio usuario'}), 400
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Usuario {user.username} eliminado'})


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


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
