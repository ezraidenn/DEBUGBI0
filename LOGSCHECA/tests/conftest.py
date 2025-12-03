"""
Configuración de pytest y fixtures compartidos.
"""
import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from webapp.app import socketio
from webapp.models import db, User
from src.utils.config import Config


@pytest.fixture(scope='session')
def app():
    """Crea una instancia de la aplicación para testing."""
    from webapp.app import app as flask_app
    
    # Configuración de testing
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    
    # Deshabilitar caché en tests
    flask_app.config['CACHE_ENABLED'] = False
    
    # Crear tablas
    with flask_app.app_context():
        db.create_all()
        
        # Crear usuario de prueba
        test_user = User(
            username='testuser',
            email='test@example.com',
            full_name='Test User',
            is_admin=False
        )
        test_user.set_password('testpass123')
        
        test_admin = User(
            username='testadmin',
            email='admin@example.com',
            full_name='Test Admin',
            is_admin=True
        )
        test_admin.set_password('adminpass123')
        
        db.session.add(test_user)
        db.session.add(test_admin)
        db.session.commit()
    
    yield flask_app
    
    # Cleanup
    with flask_app.app_context():
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Crea un cliente de testing."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Crea un runner de CLI."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def auth_client(client):
    """Cliente autenticado como usuario normal."""
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass123'
    })
    return client


@pytest.fixture(scope='function')
def admin_client(client):
    """Cliente autenticado como admin."""
    client.post('/login', data={
        'username': 'testadmin',
        'password': 'adminpass123'
    })
    return client


@pytest.fixture(scope='function')
def db_session(app):
    """Sesión de base de datos para tests."""
    with app.app_context():
        yield db.session
        db.session.rollback()


@pytest.fixture
def mock_biostar_config():
    """Mock de configuración de BioStar."""
    return Config()


@pytest.fixture
def sample_device():
    """Dispositivo de ejemplo para tests."""
    return {
        'id': 542192209,
        'name': 'Test Device',
        'alias': 'Test Checador',
        'status': 'online'
    }


@pytest.fixture
def sample_event():
    """Evento de ejemplo para tests."""
    from datetime import datetime
    return {
        'id': 12345,
        'datetime': datetime.now(),
        'event_code': '4097',
        'event_type': 'VERIFY_SUCCESS',
        'user_id': 'TEST001',
        'device_id': 542192209
    }


@pytest.fixture
def sample_events_list():
    """Lista de eventos de ejemplo."""
    from datetime import datetime, timedelta
    base_time = datetime.now()
    
    return [
        {
            'id': i,
            'datetime': base_time + timedelta(minutes=i),
            'event_code': '4097' if i % 2 == 0 else '4353',
            'event_type': 'VERIFY_SUCCESS' if i % 2 == 0 else 'VERIFY_FAIL',
            'user_id': f'USER{i:03d}',
            'device_id': 542192209
        }
        for i in range(10)
    ]
