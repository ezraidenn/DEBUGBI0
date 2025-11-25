"""
Tests de autenticación y autorización.
"""
import pytest
from flask import url_for


class TestAuthentication:
    """Tests de autenticación."""
    
    def test_login_page_loads(self, client):
        """Test de carga de página de login."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    def test_successful_login(self, client):
        """Test de login exitoso."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'dashboard' in response.data.lower() or b'dispositivos' in response.data.lower()
    
    def test_failed_login_wrong_password(self, client):
        """Test de login fallido con contraseña incorrecta."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'incorrectos' in response.data.lower() or b'invalid' in response.data.lower()
    
    def test_failed_login_wrong_username(self, client):
        """Test de login fallido con usuario inexistente."""
        response = client.post('/login', data={
            'username': 'nonexistent',
            'password': 'anypassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'incorrectos' in response.data.lower() or b'invalid' in response.data.lower()
    
    def test_logout(self, auth_client):
        """Test de logout."""
        response = auth_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    def test_dashboard_requires_login(self, client):
        """Test de que dashboard requiere autenticación."""
        response = client.get('/dashboard')
        assert response.status_code == 302  # Redirect to login
    
    def test_dashboard_accessible_when_logged_in(self, auth_client):
        """Test de acceso a dashboard cuando está autenticado."""
        response = auth_client.get('/dashboard')
        assert response.status_code == 200


class TestAuthorization:
    """Tests de autorización."""
    
    def test_regular_user_cannot_access_users_list(self, auth_client):
        """Test de que usuario regular no puede acceder a gestión de usuarios."""
        response = auth_client.get('/users', follow_redirects=True)
        assert response.status_code == 200
        assert b'permisos' in response.data.lower() or b'permission' in response.data.lower()
    
    def test_admin_can_access_users_list(self, admin_client):
        """Test de que admin puede acceder a gestión de usuarios."""
        response = admin_client.get('/users')
        assert response.status_code == 200
    
    def test_regular_user_cannot_create_user(self, auth_client):
        """Test de que usuario regular no puede crear usuarios."""
        response = auth_client.get('/users/create', follow_redirects=True)
        assert response.status_code == 200
        assert b'permisos' in response.data.lower() or b'permission' in response.data.lower()
    
    def test_admin_can_create_user(self, admin_client):
        """Test de que admin puede crear usuarios."""
        response = admin_client.get('/users/create')
        assert response.status_code == 200


class TestSessionManagement:
    """Tests de gestión de sesiones."""
    
    def test_remember_me_functionality(self, client):
        """Test de funcionalidad 'recordarme'."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass123',
            'remember': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_redirect_after_login(self, client):
        """Test de redirección después de login."""
        # Intentar acceder a página protegida
        client.get('/dashboard')
        
        # Login
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass123'
        }, follow_redirects=False)
        
        # Debe redirigir
        assert response.status_code == 302
