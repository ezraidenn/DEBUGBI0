"""
Tests para el sistema de monitoreo.
"""
import pytest
from webapp.monitoring import HealthChecker, monitor_error, monitor_event


class TestHealthChecker:
    """Tests para HealthChecker."""
    
    @pytest.fixture
    def health_checker(self, app):
        """Fixture de health checker."""
        return HealthChecker(app)
    
    def test_health_checker_initialization(self, health_checker):
        """Test de inicialización."""
        assert health_checker is not None
        assert len(health_checker.checks) > 0
    
    def test_system_check(self, health_checker):
        """Test de verificación del sistema."""
        status, message = health_checker._check_system()
        assert isinstance(status, bool)
        assert isinstance(message, str)
    
    def test_database_check(self, health_checker):
        """Test de verificación de base de datos."""
        status, message = health_checker._check_database()
        assert isinstance(status, bool)
        assert isinstance(message, str)
    
    def test_cache_check(self, health_checker):
        """Test de verificación de caché."""
        status, message = health_checker._check_cache()
        assert isinstance(status, bool)
        assert isinstance(message, str)
    
    def test_run_all_checks(self, health_checker):
        """Test de ejecutar todos los checks."""
        results = health_checker.run_all_checks()
        
        assert 'status' in results
        assert 'timestamp' in results
        assert 'checks' in results
        assert results['status'] in ['healthy', 'unhealthy']
    
    def test_get_metrics(self, health_checker):
        """Test de obtener métricas."""
        metrics = health_checker.get_metrics()
        
        assert 'system' in metrics or 'error' in metrics
        if 'system' in metrics:
            assert 'cpu_percent' in metrics['system']
            assert 'memory_percent' in metrics['system']
    
    def test_register_custom_check(self, health_checker):
        """Test de registrar check personalizado."""
        def custom_check():
            return True, "Custom check passed"
        
        health_checker.register_check('custom', custom_check)
        assert 'custom' in health_checker.checks
        
        results = health_checker.run_all_checks()
        assert 'custom' in results['checks']


class TestHealthEndpoints:
    """Tests para endpoints de health."""
    
    def test_health_endpoint(self, client):
        """Test del endpoint /health."""
        response = client.get('/health')
        assert response.status_code in [200, 503]
        
        data = response.get_json()
        assert 'status' in data
        assert 'checks' in data
    
    def test_readiness_endpoint(self, client):
        """Test del endpoint /health/ready."""
        response = client.get('/health/ready')
        assert response.status_code in [200, 503]
        
        data = response.get_json()
        assert 'ready' in data
    
    def test_liveness_endpoint(self, client):
        """Test del endpoint /health/live."""
        response = client.get('/health/live')
        assert response.status_code in [200, 503]
        
        data = response.get_json()
        assert 'alive' in data
    
    def test_metrics_app_endpoint(self, client):
        """Test del endpoint /metrics/app."""
        response = client.get('/metrics/app')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'system' in data or 'error' in data


class TestMonitoringFunctions:
    """Tests para funciones de monitoreo."""
    
    def test_monitor_error(self):
        """Test de registro de errores."""
        # No debe lanzar excepción
        monitor_error('test_error')
        monitor_error('database_error')
    
    def test_monitor_event(self):
        """Test de registro de eventos."""
        # No debe lanzar excepción
        monitor_event(12345, 'ACCESS_GRANTED')
        monitor_event(67890, 'ACCESS_DENIED')
