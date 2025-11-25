"""
Sistema de monitoreo y health checks para la aplicación.
Incluye métricas de Prometheus y endpoints de salud.
"""
import time
import psutil
import logging
from datetime import datetime
from functools import wraps
from typing import Callable, Dict, Any
from flask import request, g

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)


# ==================== MÉTRICAS DE PROMETHEUS ====================

if PROMETHEUS_AVAILABLE:
    # Contador de requests HTTP
    http_requests_total = Counter(
        'http_requests_total',
        'Total de requests HTTP',
        ['method', 'endpoint', 'status']
    )
    
    # Histograma de latencia de requests
    http_request_duration_seconds = Histogram(
        'http_request_duration_seconds',
        'Duración de requests HTTP en segundos',
        ['method', 'endpoint']
    )
    
    # Gauge de usuarios activos
    active_users = Gauge(
        'active_users',
        'Número de usuarios activos'
    )
    
    # Gauge de dispositivos monitoreados
    monitored_devices = Gauge(
        'monitored_devices',
        'Número de dispositivos siendo monitoreados'
    )
    
    # Contador de eventos procesados
    events_processed_total = Counter(
        'events_processed_total',
        'Total de eventos procesados',
        ['device_id', 'event_type']
    )
    
    # Gauge de uso de memoria
    memory_usage_bytes = Gauge(
        'memory_usage_bytes',
        'Uso de memoria en bytes'
    )
    
    # Gauge de uso de CPU
    cpu_usage_percent = Gauge(
        'cpu_usage_percent',
        'Uso de CPU en porcentaje'
    )
    
    # Contador de errores
    errors_total = Counter(
        'errors_total',
        'Total de errores',
        ['error_type']
    )


# ==================== DECORADORES DE MONITOREO ====================

def monitor_request(func: Callable) -> Callable:
    """Decorador para monitorear requests HTTP."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not PROMETHEUS_AVAILABLE:
            return func(*args, **kwargs)
        
        # Guardar tiempo de inicio
        g.start_time = time.time()
        
        # Ejecutar función
        response = func(*args, **kwargs)
        
        # Calcular duración
        duration = time.time() - g.start_time
        
        # Obtener información del request
        endpoint = request.endpoint or 'unknown'
        method = request.method
        status = getattr(response, 'status_code', 200)
        
        # Registrar métricas
        http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
        
        return response
    
    return wrapper


def monitor_error(error_type: str):
    """Registra un error en las métricas."""
    if PROMETHEUS_AVAILABLE:
        errors_total.labels(error_type=error_type).inc()


def monitor_event(device_id: int, event_type: str):
    """Registra un evento procesado en las métricas."""
    if PROMETHEUS_AVAILABLE:
        events_processed_total.labels(device_id=str(device_id), event_type=event_type).inc()


# ==================== HEALTH CHECKS ====================

class HealthChecker:
    """Gestor de health checks para la aplicación."""
    
    def __init__(self, app=None):
        """Inicializa el health checker."""
        self.app = app
        self.checks = {}
        
        # Registrar checks básicos
        self.register_check('system', self._check_system)
        self.register_check('database', self._check_database)
        self.register_check('cache', self._check_cache)
        self.register_check('biostar', self._check_biostar)
    
    def register_check(self, name: str, check_func: Callable) -> None:
        """
        Registra un nuevo health check.
        
        Args:
            name: Nombre del check
            check_func: Función que retorna (bool, str) - (status, message)
        """
        self.checks[name] = check_func
    
    def _check_system(self) -> tuple:
        """Verifica el estado del sistema."""
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Actualizar métricas
            if PROMETHEUS_AVAILABLE:
                memory_usage_bytes.set(memory.used)
                cpu_usage_percent.set(cpu)
            
            # Verificar umbrales
            if memory.percent > 90:
                return False, f"Memoria alta: {memory.percent}%"
            if cpu > 90:
                return False, f"CPU alta: {cpu}%"
            if disk.percent > 90:
                return False, f"Disco lleno: {disk.percent}%"
            
            return True, f"CPU: {cpu}%, RAM: {memory.percent}%, Disco: {disk.percent}%"
        except Exception as e:
            return False, f"Error al verificar sistema: {str(e)}"
    
    def _check_database(self) -> tuple:
        """Verifica la conexión a la base de datos."""
        try:
            from webapp.models import db, User
            # Intentar una query simple
            User.query.first()
            return True, "Base de datos conectada"
        except Exception as e:
            return False, f"Error de base de datos: {str(e)}"
    
    def _check_cache(self) -> tuple:
        """Verifica el estado del caché."""
        try:
            if not self.app:
                return True, "Cache no configurado"
            
            cache_manager = self.app.extensions.get('cache_manager')
            if not cache_manager:
                return True, "Cache no habilitado"
            
            stats = cache_manager.get_stats()
            if stats['enabled']:
                return True, f"Cache activo ({stats['backend']}): {stats['keys_count']} keys"
            else:
                return True, "Cache deshabilitado"
        except Exception as e:
            return False, f"Error de caché: {str(e)}"
    
    def _check_biostar(self) -> tuple:
        """Verifica la conexión con BioStar."""
        try:
            from src.utils.config import Config
            from src.api.biostar_client import BioStarAPIClient
            
            config = Config()
            client = BioStarAPIClient(config)
            
            if client.login():
                return True, "BioStar conectado"
            else:
                return False, "No se pudo autenticar con BioStar"
        except Exception as e:
            return False, f"Error de BioStar: {str(e)}"
    
    def run_all_checks(self) -> Dict[str, Any]:
        """
        Ejecuta todos los health checks registrados.
        
        Returns:
            Dict con el estado de cada check
        """
        results = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        for name, check_func in self.checks.items():
            try:
                status, message = check_func()
                results['checks'][name] = {
                    'status': 'pass' if status else 'fail',
                    'message': message
                }
                
                if not status:
                    results['status'] = 'unhealthy'
                    
            except Exception as e:
                results['checks'][name] = {
                    'status': 'error',
                    'message': str(e)
                }
                results['status'] = 'unhealthy'
        
        return results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del sistema."""
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Información de procesos
            process = psutil.Process()
            
            return {
                'system': {
                    'cpu_percent': cpu,
                    'memory_percent': memory.percent,
                    'memory_used_mb': memory.used / (1024 * 1024),
                    'memory_total_mb': memory.total / (1024 * 1024),
                    'disk_percent': disk.percent,
                    'disk_used_gb': disk.used / (1024 * 1024 * 1024),
                    'disk_total_gb': disk.total / (1024 * 1024 * 1024),
                },
                'process': {
                    'memory_mb': process.memory_info().rss / (1024 * 1024),
                    'cpu_percent': process.cpu_percent(interval=0.1),
                    'threads': process.num_threads(),
                    'open_files': len(process.open_files()),
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error al obtener métricas: {e}")
            return {'error': str(e)}


# ==================== INICIALIZACIÓN ====================

health_checker: HealthChecker = None


def init_monitoring(app):
    """
    Inicializa el sistema de monitoreo en la aplicación Flask.
    
    Args:
        app: Instancia de Flask
    """
    global health_checker
    
    health_checker = HealthChecker(app)
    app.extensions['health_checker'] = health_checker
    
    logger.info("✓ Sistema de monitoreo inicializado")
    
    # Registrar rutas de monitoreo
    @app.route('/health')
    def health_check():
        """Endpoint de health check."""
        from flask import jsonify
        results = health_checker.run_all_checks()
        status_code = 200 if results['status'] == 'healthy' else 503
        return jsonify(results), status_code
    
    @app.route('/health/ready')
    def readiness_check():
        """Endpoint de readiness (listo para recibir tráfico)."""
        from flask import jsonify
        # Check críticos: database y biostar
        db_status, db_msg = health_checker._check_database()
        biostar_status, biostar_msg = health_checker._check_biostar()
        
        ready = db_status and biostar_status
        
        return jsonify({
            'ready': ready,
            'database': {'status': db_status, 'message': db_msg},
            'biostar': {'status': biostar_status, 'message': biostar_msg}
        }), 200 if ready else 503
    
    @app.route('/health/live')
    def liveness_check():
        """Endpoint de liveness (aplicación viva)."""
        from flask import jsonify
        # Check básico: sistema
        system_status, system_msg = health_checker._check_system()
        
        return jsonify({
            'alive': system_status,
            'message': system_msg
        }), 200 if system_status else 503
    
    @app.route('/metrics')
    def metrics_endpoint():
        """Endpoint de métricas de Prometheus."""
        if not PROMETHEUS_AVAILABLE:
            from flask import jsonify
            return jsonify({'error': 'Prometheus no disponible'}), 501
        
        from flask import Response
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
    
    @app.route('/metrics/app')
    def app_metrics():
        """Endpoint de métricas de la aplicación."""
        from flask import jsonify
        return jsonify(health_checker.get_metrics())
    
    logger.info("✓ Endpoints de monitoreo registrados: /health, /health/ready, /health/live, /metrics, /metrics/app")
    
    return health_checker
