"""
Tests unitarios para modelos de base de datos.
"""
import pytest
from datetime import datetime
from webapp.models import User, db


class TestUserModel:
    """Tests para el modelo User."""
    
    def test_user_creation(self, app, db_session):
        """Test de creación de usuario."""
        user = User(
            username='newuser',
            email='newuser@example.com',
            full_name='New User'
        )
        user.set_password('password123')
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == 'newuser'
        assert user.email == 'newuser@example.com'
        assert user.is_admin is False
        assert user.is_active is True
    
    def test_password_hashing(self, app):
        """Test de hashing de contraseñas."""
        user = User(username='testuser', email='test@test.com')
        user.set_password('mypassword')
        
        assert user.password_hash != 'mypassword'
        assert user.check_password('mypassword') is True
        assert user.check_password('wrongpassword') is False
    
    def test_unique_username(self, app, db_session):
        """Test de username único."""
        user1 = User(username='duplicate', email='user1@test.com')
        user1.set_password('pass123')
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(username='duplicate', email='user2@test.com')
        user2.set_password('pass123')
        db_session.add(user2)
        
        with pytest.raises(Exception):
            db_session.commit()
    
    def test_unique_email(self, app, db_session):
        """Test de email único."""
        user1 = User(username='user1', email='duplicate@test.com')
        user1.set_password('pass123')
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(username='user2', email='duplicate@test.com')
        user2.set_password('pass123')
        db_session.add(user2)
        
        with pytest.raises(Exception):
            db_session.commit()
    
    def test_update_last_login(self, app, db_session):
        """Test de actualización de último login."""
        user = User(username='logintest', email='login@test.com')
        user.set_password('pass123')
        db_session.add(user)
        db_session.commit()
        
        assert user.last_login is None
        
        user.update_last_login()
        
        assert user.last_login is not None
        assert isinstance(user.last_login, datetime)
    
    def test_user_repr(self, app):
        """Test de representación string del usuario."""
        user = User(username='reprtest', email='repr@test.com')
        assert repr(user) == '<User reprtest>'
    
    def test_admin_flag(self, app, db_session):
        """Test de flag de administrador."""
        admin = User(username='admin_test', email='admin_test@test.com', is_admin=True)
        admin.set_password('admin123')
        db_session.add(admin)
        db_session.commit()
        
        assert admin.is_admin is True
        
        regular = User(username='regular_test', email='regular_test@test.com')
        regular.set_password('pass123')
        db_session.add(regular)
        db_session.commit()
        
        assert regular.is_admin is False
    
    def test_active_flag(self, app, db_session):
        """Test de flag de usuario activo."""
        user = User(username='activetest', email='active@test.com')
        user.set_password('pass123')
        db_session.add(user)
        db_session.commit()
        
        assert user.is_active is True
        
        user.is_active = False
        db_session.commit()
        
        assert user.is_active is False
