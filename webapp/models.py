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
    """User model for authentication."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Nuevos campos de permisos
    can_see_all_events = db.Column(db.Boolean, default=False)   # Ver eventos no-concedidos
    can_manage_devices = db.Column(db.Boolean, default=False)   # Acceso a config dispositivos
    
    # Relación con permisos de dispositivos
    device_permissions = db.relationship('UserDevicePermission', backref='user', 
                                         lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password is correct."""
        return check_password_hash(self.password_hash, password)
    
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
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@biostar.local',
                full_name='Administrador',
                is_admin=True,
                can_see_all_events=True,
                can_manage_devices=True
            )
            admin.set_password('admin123')  # Cambiar en producción
            db.session.add(admin)
            print("[OK] Usuario admin creado (usuario: admin, password: admin123)")
        else:
            # Actualizar admin existente con nuevos permisos
            if not admin.can_see_all_events:
                admin.can_see_all_events = True
            if not admin.can_manage_devices:
                admin.can_manage_devices = True
        
        db.session.commit()
