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

from webapp.models import db, User, init_db
from webapp.realtime_monitor import RealtimeMonitor
from src.api.device_monitor import DeviceMonitor, EVENT_CODES
from src.utils.config import Config

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

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize database
init_db(app)

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


# ==================== DASHBOARD ROUTES ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard."""
    # Get monitor instance
    monitor = get_monitor()
    if not monitor:
        flash('Error al conectar con BioStar. Verifica la configuración.', 'danger')
        return render_template('dashboard.html', devices=[], error=True)
    
    # Get all devices
    devices = monitor.get_all_devices(refresh=True)
    
    # Get summary for each device
    devices_with_summary = []
    for device in devices:
        summary = monitor.get_debug_summary(device['id'])
        device['summary'] = summary
        devices_with_summary.append(device)
    
    return render_template('dashboard.html', devices=devices_with_summary)


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
    
    # Get all devices first to populate cache
    all_devices = monitor.get_all_devices(refresh=True)
    print(f"DEBUG: Total devices: {len(all_devices)}")
    print(f"DEBUG: Looking for device_id: {device_id}")
    print(f"DEBUG: Device IDs available: {[d['id'] for d in all_devices]}")
    
    # Get device info
    device = monitor.get_device_by_id(device_id)
    
    if not device:
        print(f"DEBUG: Device {device_id} NOT FOUND")
        flash(f'Dispositivo {device_id} no encontrado.', 'danger')
        return redirect(url_for('dashboard'))
    
    print(f"DEBUG: Device found: {device['name']}")
    
    # Get events and filter by time (5:30 AM - 11:59 PM)
    events = monitor.get_device_events_today(device_id)
    print(f"DEBUG: Total events before filter: {len(events)}")
    
    # Log some event times before filter
    print("DEBUG: Sample times BEFORE filter (first 5):")
    for i, e in enumerate(events[:5]):
        if e.get('datetime'):
            local_t = utc_to_local(e['datetime'])
            if local_t:
                print(f"  Event {i+1}: {local_t.strftime('%H:%M:%S')}")
    
    events = filter_events_by_time(events)
    print(f"DEBUG: Total events after filter: {len(events)}")
    print(f"DEBUG: Filtered out: {336 - len(events)} events")
    
    # Log some event times after filter
    print("DEBUG: Sample times AFTER filter (first 5):")
    for i, e in enumerate(events[:5]):
        if e.get('datetime'):
            local_t = utc_to_local(e['datetime'])
            if local_t:
                print(f"  Event {i+1}: {local_t.strftime('%H:%M:%S')}")
    
    # Calculate first and last event BEFORE converting to local
    first_event_dt = None
    last_event_dt = None
    if events:
        for event in events:
            event_dt = event.get('datetime')
            if event_dt:
                # Convert to datetime if string
                if isinstance(event_dt, str):
                    from dateutil import parser
                    event_dt = parser.parse(event_dt)
                
                if not first_event_dt or event_dt < first_event_dt:
                    first_event_dt = event_dt
                if not last_event_dt or event_dt > last_event_dt:
                    last_event_dt = event_dt
    
    # Convert datetime to local time for display
    for event in events:
        if event.get('datetime'):
            local_time = utc_to_local(event['datetime'])
            event['datetime'] = local_time
    
    df = monitor.events_to_dataframe(events)
    
    # Convert to list of dicts for template
    events_list = df.to_dict('records') if not df.empty else []
    
    # Get summary and override with filtered event times
    summary = monitor.get_debug_summary(device_id)
    
    # Override first/last with filtered events
    if first_event_dt:
        summary['first_event'] = utc_to_local(first_event_dt)
        print(f"DEBUG: First event (local): {summary['first_event'].strftime('%H:%M:%S')}")
    else:
        summary['first_event'] = None
        
    if last_event_dt:
        summary['last_event'] = utc_to_local(last_event_dt)
        print(f"DEBUG: Last event (local): {summary['last_event'].strftime('%H:%M:%S')}")
    else:
        summary['last_event'] = None
    
    return render_template('debug_device.html', 
                         device=device, 
                         events=events_list, 
                         summary=summary)


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
            event_list = [{
                'datetime': format_local_time(e.get('datetime')),
                'user': e.get('user_id', 'N/A'),
                'event_type': classify_event(e.get('event_code', '0'))[1],
                'event_code': e.get('event_code', 'N/A')
            } for e in events[-50:]]  # Last 50 events
            
            return jsonify({
                'title': 'Total de Eventos',
                'subtitle': f'{device.get("alias") or device.get("name")}',
                'count': len(events),
                'data': event_list[::-1]  # Reverse to show newest first
            })
        
        elif stat_type == 'granted':
            # Access granted events
            granted_events = [e for e in events if e.get('event_code') in EVENT_CODES['access_granted']]
            event_list = [{
                'datetime': format_local_time(e.get('datetime')),
                'user': e.get('user_id', 'N/A'),
                'door': e.get('door_name', 'N/A')
            } for e in granted_events[-50:]]
            
            return jsonify({
                'title': 'Accesos Concedidos',
                'subtitle': f'{device.get("alias") or device.get("name")}',
                'count': len(granted_events),
                'data': event_list[::-1]
            })
        
        elif stat_type == 'denied':
            # Access denied events
            denied_events = [e for e in events if e.get('event_code') in EVENT_CODES['access_denied']]
            event_list = [{
                'datetime': format_local_time(e.get('datetime')),
                'user': e.get('user_id', 'N/A'),
                'reason': classify_event(e.get('event_code', '0'))[1]
            } for e in denied_events[-50:]]
            
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
                user_id = e.get('user_id')
                if user_id and user_id != 'N/A':
                    user_ids.add(user_id)
                    if user_id not in user_events:
                        user_events[user_id] = {
                            'user_id': user_id,
                            'total_events': 0,
                            'granted': 0,
                            'denied': 0,
                            'last_access': None
                        }
                    
                    user_events[user_id]['total_events'] += 1
                    
                    if e.get('event_code') in EVENT_CODES['access_granted']:
                        user_events[user_id]['granted'] += 1
                    elif e.get('event_code') in EVENT_CODES['access_denied']:
                        user_events[user_id]['denied'] += 1
                    
                    event_time = e.get('datetime')
                    if event_time:
                        if not user_events[user_id]['last_access'] or event_time > user_events[user_id]['last_access']:
                            user_events[user_id]['last_access'] = event_time
            
            # Format user data
            user_list = []
            for user_data in user_events.values():
                last_access = format_local_time(user_data['last_access'])
                
                user_list.append({
                    'user_id': user_data['user_id'],
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
            is_admin=is_admin
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Usuario {username} creado exitosamente.', 'success')
        return redirect(url_for('users_list'))
    
    return render_template('user_form.html', user=None, action='create')


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
        
        # Update password if provided
        password = request.form.get('password')
        if password:
            user.set_password(password)
        
        db.session.commit()
        flash(f'Usuario {user.username} actualizado exitosamente.', 'success')
        return redirect(url_for('users_list'))
    
    return render_template('user_form.html', user=user, action='edit')


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


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
