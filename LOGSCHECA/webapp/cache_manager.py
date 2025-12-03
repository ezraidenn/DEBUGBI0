"""
Sistema de caché inteligente con Redis para optimizar performance.
Incluye estrategias de invalidación y TTL configurables.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Callable
from functools import wraps
import hashlib

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheManager:
    """Gestor de caché con Redis y fallback a memoria."""
    
    def __init__(self, redis_url: str = 'redis://localhost:6379/0', enabled: bool = True):
        """
        Inicializa el gestor de caché.
        
        Args:
            redis_url: URL de conexión a Redis
            enabled: Si el caché está habilitado
        """
        self.enabled = enabled and REDIS_AVAILABLE
        self.redis_client = None
        self.memory_cache = {}  # Fallback cache
        
        if self.enabled:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                # Test connection
                self.redis_client.ping()
                logger.info("✓ Redis conectado exitosamente")
            except Exception as e:
                logger.warning(f"⚠ Redis no disponible, usando caché en memoria: {e}")
                self.redis_client = None
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Genera una clave única para el caché."""
        key_parts = [prefix] + [str(arg) for arg in args]
        if kwargs:
            key_parts.append(hashlib.md5(json.dumps(kwargs, sort_keys=True).encode()).hexdigest())
        return ':'.join(key_parts)
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché."""
        if not self.enabled:
            return None
        
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                # Fallback a memoria
                if key in self.memory_cache:
                    item = self.memory_cache[key]
                    if item['expires_at'] > datetime.now():
                        return item['value']
                    else:
                        del self.memory_cache[key]
        except Exception as e:
            logger.error(f"Error al obtener del caché: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Guarda un valor en el caché.
        
        Args:
            key: Clave del caché
            value: Valor a guardar
            ttl: Tiempo de vida en segundos (default: 5 minutos)
        """
        if not self.enabled:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            
            if self.redis_client:
                self.redis_client.setex(key, ttl, serialized)
            else:
                # Fallback a memoria
                self.memory_cache[key] = {
                    'value': value,
                    'expires_at': datetime.now() + timedelta(seconds=ttl)
                }
            
            return True
        except Exception as e:
            logger.error(f"Error al guardar en caché: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Elimina una clave del caché."""
        if not self.enabled:
            return False
        
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                self.memory_cache.pop(key, None)
            return True
        except Exception as e:
            logger.error(f"Error al eliminar del caché: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Elimina todas las claves que coincidan con el patrón."""
        if not self.enabled:
            return 0
        
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
            else:
                # Fallback a memoria
                keys_to_delete = [k for k in self.memory_cache.keys() if pattern.replace('*', '') in k]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                return len(keys_to_delete)
        except Exception as e:
            logger.error(f"Error al eliminar patrón del caché: {e}")
        
        return 0
    
    def clear_all(self) -> bool:
        """Limpia todo el caché."""
        if not self.enabled:
            return False
        
        try:
            if self.redis_client:
                self.redis_client.flushdb()
            else:
                self.memory_cache.clear()
            logger.info("✓ Caché limpiado completamente")
            return True
        except Exception as e:
            logger.error(f"Error al limpiar caché: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Obtiene estadísticas del caché."""
        stats = {
            'enabled': self.enabled,
            'backend': 'redis' if self.redis_client else 'memory',
            'keys_count': 0,
            'memory_usage': 0
        }
        
        try:
            if self.redis_client:
                info = self.redis_client.info('memory')
                stats['keys_count'] = self.redis_client.dbsize()
                stats['memory_usage'] = info.get('used_memory_human', 'N/A')
            else:
                stats['keys_count'] = len(self.memory_cache)
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
        
        return stats


def cached(ttl: int = 300, key_prefix: str = 'cache'):
    """
    Decorador para cachear resultados de funciones.
    
    Args:
        ttl: Tiempo de vida en segundos
        key_prefix: Prefijo para la clave del caché
    
    Example:
        @cached(ttl=600, key_prefix='devices')
        def get_all_devices():
            return expensive_operation()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Obtener instancia de cache_manager del contexto de Flask
            from flask import current_app
            cache_manager = current_app.extensions.get('cache_manager')
            
            if not cache_manager or not cache_manager.enabled:
                return func(*args, **kwargs)
            
            # Generar clave única
            cache_key = cache_manager._generate_key(
                f"{key_prefix}:{func.__name__}",
                *args,
                **kwargs
            )
            
            # Intentar obtener del caché
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"✓ Cache hit: {cache_key}")
                return cached_value
            
            # Ejecutar función y cachear resultado
            logger.debug(f"✗ Cache miss: {cache_key}")
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


# Instancia global (se inicializa en app.py)
cache_manager: Optional[CacheManager] = None


def init_cache(app, redis_url: str = None, enabled: bool = True):
    """
    Inicializa el sistema de caché en la aplicación Flask.
    
    Args:
        app: Instancia de Flask
        redis_url: URL de Redis (default: redis://localhost:6379/0)
        enabled: Si el caché está habilitado
    """
    global cache_manager
    
    if redis_url is None:
        redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    
    cache_manager = CacheManager(redis_url=redis_url, enabled=enabled)
    app.extensions['cache_manager'] = cache_manager
    
    logger.info(f"✓ Sistema de caché inicializado: {cache_manager.get_stats()}")
    
    return cache_manager
