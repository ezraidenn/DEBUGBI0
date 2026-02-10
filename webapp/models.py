"""
Database models for the web application.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


# ============================================
# DEVICE CONFIGURATION MODELS
# ============================================

class DeviceCategory(db.Model):
    """Categorías/etiquetas para agrupar dispositivos."""
    
    __tablename__ = 'device_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(7), default='#6c757d')  # Color hex para UI
    icon = db.Column(db.String(50), default='bi-hdd')   # Bootstrap icon
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    devices = db.relationship('DeviceConfig', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<DeviceCategory {self.name}>'


class DeviceConfig(db.Model):
    """Configuración local de dispositivos BioStar."""
    
    __tablename__ = 'device_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, unique=True, nullable=False)  # ID de BioStar
    
    # Tipo de dispositivo (afecta lógica de pares)
    DEVICE_TYPES = ['checador', 'puerta', 'facial', 'otro']
    device_type = db.Column(db.String(20), default='checador')
    
    # Categoría (grupo personalizado)
    category_id = db.Column(db.Integer, db.ForeignKey('device_categories.id'))
    
    # Información del dispositivo
    alias = db.Column(db.String(100))          # Nombre personalizado
    location = db.Column(db.String(200))       # Ubicación
    
    # Configuración de lógica
    supports_pairs = db.Column(db.Boolean, default=True)  # ¿Aplica lógica entrada/salida?
    show_all_events = db.Column(db.Boolean, default=False)  # ¿Mostrar todos los eventos?
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DeviceConfig {self.device_id}: {self.alias or "Sin nombre"}>'
    
    @property
    def display_name(self):
        """Retorna el nombre a mostrar (alias o ID)."""
        return self.alias or f'Dispositivo {self.device_id}'


class UserDevicePermission(db.Model):
    """Permisos de usuario por dispositivo."""
    
    __tablename__ = 'user_device_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    device_id = db.Column(db.Integer, nullable=False)  # ID de BioStar
    
    can_view = db.Column(db.Boolean, default=True)
    can_export = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'device_id', name='unique_user_device'),
    )
    
    def __repr__(self):
        return f'<UserDevicePermission user={self.user_id} device={self.device_id}>'


# ============================================
# USER MODEL
# ============================================

class User(UserMixin, db.Model):
    """User model for authentication - NIVEL GOBIERNO."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    is_admin = db.Column(db.Boolean, default=False)
    is_auditor = db.Column(db.Boolean, default=False)  # Nuevo rol: puede crear/cerrar solo sus emergencias
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Campos de permisos
    can_see_all_events = db.Column(db.Boolean, default=False)
    can_manage_devices = db.Column(db.Boolean, default=False)
    
    # ==================== CAMPOS DE SEGURIDAD NIVEL GOBIERNO ====================
    
    # 2FA - Two Factor Authentication
    totp_secret = db.Column(db.String(32), nullable=True)  # Clave secreta para TOTP
    totp_enabled = db.Column(db.Boolean, default=False)    # Si 2FA está activado
    
    # Password Security
    password_changed_at = db.Column(db.DateTime, default=datetime.utcnow)  # Fecha último cambio
    password_history = db.Column(db.Text, nullable=True)   # JSON con hashes anteriores
    must_change_password = db.Column(db.Boolean, default=False)  # Forzar cambio
    
    # Account Security
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)   # Bloqueo temporal
    is_permanently_locked = db.Column(db.Boolean, default=False)  # Bloqueo permanente
    last_failed_login = db.Column(db.DateTime, nullable=True)
    
    # Session Security
    session_token = db.Column(db.String(64), nullable=True)  # Token de sesión único
    
    # ==================== FIN CAMPOS DE SEGURIDAD ====================
    
    # Relación con permisos de dispositivos
    device_permissions = db.relationship('UserDevicePermission', backref='user', 
                                         lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password, save_history=True):
        """Hash and set password con historial."""
        old_hash = self.password_hash
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()
        self.must_change_password = False
        
        # Guardar en historial si es necesario
        if save_history and old_hash:
            import json
            try:
                history = json.loads(self.password_history) if self.password_history else []
            except (json.JSONDecodeError, TypeError):
                history = []
            history.insert(0, old_hash)
            self.password_history = json.dumps(history[:5])  # Últimas 5
    
    def check_password(self, password):
        """Check if password is correct."""
        return check_password_hash(self.password_hash, password)
    
    def check_password_reuse(self, new_password) -> bool:
        """Verifica si la contraseña ya fue usada. Retorna True si es reutilizada."""
        import json
        if not self.password_history:
            return False
        
        try:
            history = json.loads(self.password_history)
            for old_hash in history:
                if check_password_hash(old_hash, new_password):
                    return True
        except (json.JSONDecodeError, TypeError):
            pass
        
        return False
    
    def is_password_expired(self, max_age_days=90) -> bool:
        """Verifica si la contraseña ha expirado."""
        if not self.password_changed_at:
            return True
        age_days = (datetime.utcnow() - self.password_changed_at).days
        return age_days >= max_age_days
    
    def record_failed_login(self):
        """Registra intento fallido de login."""
        self.failed_login_attempts += 1
        self.last_failed_login = datetime.utcnow()
        db.session.commit()
    
    def reset_failed_attempts(self):
        """Resetea contador de intentos fallidos."""
        self.failed_login_attempts = 0
        self.last_failed_login = None
        db.session.commit()
    
    def lock_temporarily(self, minutes=15):
        """Bloquea la cuenta temporalmente."""
        from datetime import timedelta
        self.locked_until = datetime.utcnow() + timedelta(minutes=minutes)
        db.session.commit()
    
    def is_locked(self) -> bool:
        """Verifica si la cuenta está bloqueada."""
        if self.is_permanently_locked:
            return True
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        return False
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def can_view_device(self, device_id):
        """Verifica si el usuario puede ver un dispositivo."""
        if self.is_admin:
            return True
        permission = self.device_permissions.filter_by(device_id=device_id, can_view=True).first()
        return permission is not None
    
    def get_allowed_device_ids(self):
        """Retorna lista de IDs de dispositivos que el usuario puede ver."""
        if self.is_admin:
            return None  # None significa "todos"
        return [p.device_id for p in self.device_permissions.filter_by(can_view=True).all()]
    
    def can_manage_emergencies(self):
        """Verifica si el usuario puede gestionar emergencias."""
        return self.is_admin or self.is_auditor
    
    def can_close_emergency(self, emergency):
        """Verifica si el usuario puede cerrar una emergencia específica."""
        if self.is_admin:
            return True  # Admin puede cerrar cualquier emergencia
        if self.is_auditor and emergency.started_by == self.id:
            return True  # Auditor solo puede cerrar sus propias emergencias
        return False
    
    def __repr__(self):
        return f'<User {self.username}>'


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_or_create_device_config(device_id, device_name=None, location=None):
    """Obtiene o crea la configuración de un dispositivo."""
    config = DeviceConfig.query.filter_by(device_id=device_id).first()
    if not config:
        config = DeviceConfig(
            device_id=device_id,
            alias=device_name,
            location=location,
            device_type='checador',
            supports_pairs=True
        )
        db.session.add(config)
        db.session.commit()
    return config


def init_db(app):
    """Initialize database with default data."""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # Crear categorías por defecto si no existen
        default_categories = [
            {'name': 'Checador', 'color': '#1976D2', 'icon': 'bi-fingerprint', 
             'description': 'Checador de huella/facial - Aplica lógica de pares (entrada/salida)'},
            {'name': 'Puerta', 'color': '#FF9800', 'icon': 'bi-door-open', 
             'description': 'Control de puerta - Sin lógica de pares'},
        ]
        
        for cat_data in default_categories:
            if not DeviceCategory.query.filter_by(name=cat_data['name']).first():
                category = DeviceCategory(**cat_data)
                db.session.add(category)
                print(f"[OK] Categoría '{cat_data['name']}' creada")
        
        # Crear usuario admin por defecto si no existe
        import os
        import secrets
        
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Usar contraseña de variable de entorno o generar una segura
            admin_password = os.environ.get('ADMIN_DEFAULT_PASSWORD')
            
            if not admin_password:
                # Generar contraseña segura aleatoria
                admin_password = secrets.token_urlsafe(16)
                print("=" * 60)
                print("⚠️  CONTRASEÑA ADMIN GENERADA AUTOMÁTICAMENTE")
                print(f"    Usuario: admin")
                print(f"    Contraseña: {admin_password}")
                print("    ¡GUARDA ESTA CONTRASEÑA! No se mostrará de nuevo.")
                print("    Cámbiala después del primer inicio de sesión.")
                print("=" * 60)
            
            admin = User(
                username='admin',
                email='admin@biostar.local',
                full_name='Administrador',
                is_admin=True,
                can_see_all_events=True,
                can_manage_devices=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            print("[OK] Usuario admin creado")
        else:
            # Actualizar admin existente con nuevos permisos
            if not admin.can_see_all_events:
                admin.can_see_all_events = True
            if not admin.can_manage_devices:
                admin.can_manage_devices = True
        
        db.session.commit()


# ============================================
# SISTEMA DE EMERGENCIAS
# ============================================

class Zone(db.Model):
    """Zonas físicas (Casa Club, Gimnasio, etc.)"""
    __tablename__ = 'zones'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(200))
    color = db.Column(db.String(7), default='#6c757d')
    icon = db.Column(db.String(50), default='bi-building')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    groups = db.relationship('Group', backref='zone', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Zone {self.name}>'


class Group(db.Model):
    """Grupos/Departamentos dentro de una zona (IT, Desarrollo, etc.)"""
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'), nullable=False)
    color = db.Column(db.String(7), default='#007bff')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    members = db.relationship('GroupMember', backref='group', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Group {self.name} in {self.zone.name}>'


class GroupMember(db.Model):
    """Usuarios asignados a grupos"""
    __tablename__ = 'group_members'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    biostar_user_id = db.Column(db.String(50), nullable=False)
    user_name = db.Column(db.String(200))
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('group_id', 'biostar_user_id', name='unique_group_member'),
    )
    
    def __repr__(self):
        return f'<GroupMember {self.user_name} in {self.group.name}>'


class EmergencySession(db.Model):
    """Sesión de emergencia activa"""
    __tablename__ = 'emergency_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'), nullable=False)
    emergency_type = db.Column(db.String(50), default='general')
    started_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')
    notes = db.Column(db.Text)
    unlocked_doors = db.Column(db.Text)
    
    zone = db.relationship('Zone', backref='emergencies')
    started_by_user = db.relationship('User', backref='started_emergencies')
    roll_call_entries = db.relationship('RollCallEntry', backref='emergency', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<EmergencySession {self.zone.name} - {self.status}>'


class RollCallEntry(db.Model):
    """Entrada de pase de lista"""
    __tablename__ = 'roll_call_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    emergency_id = db.Column(db.Integer, db.ForeignKey('emergency_sessions.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)  # Ahora es opcional
    biostar_user_id = db.Column(db.String(50), nullable=False)
    user_name = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
    marked_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    marked_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    manual_group_name = db.Column(db.String(200))  # Para grupos temporales (solo texto, no FK)
    
    group = db.relationship('Group', backref='roll_call_entries')
    marked_by_user = db.relationship('User', backref='marked_roll_calls')
    
    def __repr__(self):
        return f'<RollCallEntry {self.user_name} - {self.status}>'


class ZoneDevice(db.Model):
    """Dispositivos/Checadores asignados a zonas para detección automática de presencia"""
    __tablename__ = 'zone_devices'
    
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'), nullable=False)
    device_id = db.Column(db.Integer, nullable=False)
    device_name = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    zone = db.relationship('Zone', backref=db.backref('devices', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('zone_id', 'device_id', name='unique_zone_device'),
    )
    
    def __repr__(self):
        return f'<ZoneDevice {self.device_name} in zone {self.zone_id}>'


# ============================================
# SISTEMA DE BOTÓN DE PÁNICO
# ============================================

class PanicModeStatus(db.Model):
    """Estado actual del modo pánico por dispositivo"""
    __tablename__ = 'panic_mode_status'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), unique=True, nullable=False)
    device_name = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    alarm_active = db.Column(db.Boolean, default=False)
    activated_at = db.Column(db.DateTime)
    activated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    deactivated_at = db.Column(db.DateTime)
    deactivated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    activated_by = db.relationship('User', foreign_keys=[activated_by_user_id], backref='panic_activations')
    deactivated_by = db.relationship('User', foreign_keys=[deactivated_by_user_id], backref='panic_deactivations')
    
    def __repr__(self):
        return f'<PanicModeStatus {self.device_name} - {"ACTIVE" if self.is_active else "OFF"}>'


class PanicModeLog(db.Model):
    """Log de acciones del modo pánico"""
    __tablename__ = 'panic_mode_log'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), nullable=False)
    device_name = db.Column(db.String(200), nullable=False)
    action = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    success = db.Column(db.Boolean, default=True, nullable=False)
    error_message = db.Column(db.Text)
    alarm_activated = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref='panic_logs')
    
    def __repr__(self):
        return f'<PanicModeLog {self.device_name} - {self.action} by {self.username}>'


# ============================================
# SISTEMA MOBPER - MOVIMIENTO DE PERSONAL
# ============================================

class MobPerUser(db.Model):
    """Usuario del sistema MobPer (independiente del sistema principal)"""
    __tablename__ = 'mobper_users'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_socio = db.Column(db.String(20), unique=True, nullable=False)
    nombre_completo = db.Column(db.String(200), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relaciones
    preset = db.relationship('PresetUsuario', backref='user', uselist=False, cascade='all, delete-orphan')
    incidencias_dia = db.relationship('IncidenciaDia', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<MobPerUser {self.numero_socio} - {self.nombre_completo}>'

class PresetUsuario(db.Model):
    """Configuración de horarios y preferencias del usuario"""
    __tablename__ = 'mobper_presets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('mobper_users.id'), nullable=False)
    
    # Datos para el formato
    nombre_formato = db.Column(db.String(200))
    departamento_formato = db.Column(db.String(100))
    jefe_directo_nombre = db.Column(db.String(200))
    
    # Configuración de horario
    hora_entrada_default = db.Column(db.Time, default=datetime.strptime('09:00:00', '%H:%M:%S').time())
    tolerancia_segundos = db.Column(db.Integer, default=600)  # 10 minutos
    dias_descanso = db.Column(db.JSON, default=lambda: [5, 6])  # Sábado y Domingo
    lista_inhabiles = db.Column(db.JSON, default=list)
    
    vigente_desde = db.Column(db.Date, default=datetime.utcnow)
    vigente_hasta = db.Column(db.Date)
    
    def __repr__(self):
        return f'<PresetUsuario {self.user_id}>'

class MovPerPeriodo(db.Model):
    """Snapshot de una quincena procesada"""
    __tablename__ = 'mobper_periodos'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('mobper_users.id'), nullable=False)
    periodo_inicio = db.Column(db.Date, nullable=False)
    periodo_fin = db.Column(db.Date, nullable=False)
    
    preset_snapshot = db.Column(db.JSON)  # Copia del preset usado
    raw_daily_first_checkins = db.Column(db.JSON)  # {"2026-01-01": "09:05:23", ...}
    raw_daily_status_auto = db.Column(db.JSON)  # {"2026-01-01": "A_TIEMPO", ...}
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pdf_generated_at = db.Column(db.DateTime)
    pdf_hash = db.Column(db.String(64))
    
    def __repr__(self):
        return f'<MovPerPeriodo {self.periodo_inicio} - {self.periodo_fin}>'

class IncidenciaDia(db.Model):
    """Clasificación individual por día - cada día puede tener diferente justificación"""
    __tablename__ = 'mobper_incidencias_dia'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('mobper_users.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    
    # Estado automático detectado
    estado_auto = db.Column(db.String(20))  # A_TIEMPO, RETARDO, FALTA, DESCANSO, INHABIL
    
    # Clasificación manual del usuario
    # Opciones: REMOTO, GUARDIA, VACACIONES, PERMISO, INHABIL, INCAPACIDAD
    # RETARDO se justifica automáticamente
    clasificacion = db.Column(db.String(50))
    
    # Campo general: ¿Con goce de sueldo? (aplica a nivel de quincena)
    con_goce_sueldo = db.Column(db.Boolean, default=True)
    
    # Para retardos: ¿está justificado? (por defecto True - auto-justificado)
    justificado = db.Column(db.Boolean, default=True)
    
    # Motivo generado automáticamente según clasificación
    motivo_auto = db.Column(db.String(200))
    
    # Datos del registro
    hora_entrada = db.Column(db.Time)
    minutos_diferencia = db.Column(db.Integer)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índice único para evitar duplicados
    __table_args__ = (
        db.UniqueConstraint('user_id', 'fecha', name='unique_user_fecha_dia'),
    )
    
    def __repr__(self):
        return f'<IncidenciaDia {self.user_id} {self.fecha} - {self.clasificacion}>'
