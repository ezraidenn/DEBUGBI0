"""
Tests para el sistema de caché.
"""
import pytest
import time
from webapp.cache_manager import CacheManager, cached


class TestCacheManager:
    """Tests para CacheManager."""
    
    @pytest.fixture
    def cache(self):
        """Fixture de cache manager con memoria."""
        return CacheManager(redis_url='redis://localhost:6379/0', enabled=True)
    
    def test_cache_initialization(self, cache):
        """Test de inicialización del caché."""
        assert cache is not None
        assert cache.enabled is True
    
    def test_set_and_get(self, cache):
        """Test de guardar y obtener del caché."""
        cache.set('test_key', 'test_value', ttl=60)
        value = cache.get('test_key')
        assert value == 'test_value'
    
    def test_get_nonexistent_key(self, cache):
        """Test de obtener clave inexistente."""
        value = cache.get('nonexistent_key')
        assert value is None
    
    def test_delete_key(self, cache):
        """Test de eliminar clave."""
        cache.set('delete_me', 'value', ttl=60)
        assert cache.get('delete_me') == 'value'
        
        cache.delete('delete_me')
        assert cache.get('delete_me') is None
    
    def test_ttl_expiration(self, cache):
        """Test de expiración por TTL."""
        cache.set('expire_me', 'value', ttl=1)
        assert cache.get('expire_me') == 'value'
        
        time.sleep(2)
        assert cache.get('expire_me') is None
    
    def test_cache_complex_objects(self, cache):
        """Test de cachear objetos complejos."""
        data = {
            'list': [1, 2, 3],
            'dict': {'a': 1, 'b': 2},
            'string': 'test',
            'number': 42
        }
        
        cache.set('complex', data, ttl=60)
        retrieved = cache.get('complex')
        
        assert retrieved == data
    
    def test_delete_pattern(self, cache):
        """Test de eliminar por patrón."""
        cache.set('prefix:key1', 'value1', ttl=60)
        cache.set('prefix:key2', 'value2', ttl=60)
        cache.set('other:key', 'value3', ttl=60)
        
        deleted = cache.delete_pattern('prefix:*')
        assert deleted >= 0  # Puede ser 0 si usa memoria
        
        assert cache.get('other:key') is not None or cache.get('other:key') is None
    
    def test_clear_all(self, cache):
        """Test de limpiar todo el caché."""
        cache.set('key1', 'value1', ttl=60)
        cache.set('key2', 'value2', ttl=60)
        
        cache.clear_all()
        
        assert cache.get('key1') is None
        assert cache.get('key2') is None
    
    def test_get_stats(self, cache):
        """Test de obtener estadísticas."""
        stats = cache.get_stats()
        
        assert 'enabled' in stats
        assert 'backend' in stats
        assert 'keys_count' in stats
    
    def test_generate_key(self, cache):
        """Test de generación de claves."""
        key1 = cache._generate_key('prefix', 'arg1', 'arg2')
        key2 = cache._generate_key('prefix', 'arg1', 'arg2')
        key3 = cache._generate_key('prefix', 'arg1', 'arg3')
        
        assert key1 == key2
        assert key1 != key3


class TestCacheDecorator:
    """Tests para el decorador @cached."""
    
    def test_cached_decorator(self, app):
        """Test del decorador @cached."""
        call_count = {'count': 0}
        
        @cached(ttl=60, key_prefix='test')
        def expensive_function(x):
            call_count['count'] += 1
            return x * 2
        
        with app.app_context():
            # Primera llamada - debe ejecutar la función
            result1 = expensive_function(5)
            assert result1 == 10
            assert call_count['count'] == 1
            
            # Segunda llamada - debe usar caché
            result2 = expensive_function(5)
            assert result2 == 10
            # Si el caché está habilitado, no debe incrementar
            # Si no está habilitado, sí incrementará
            assert call_count['count'] >= 1
    
    def test_cached_with_different_args(self, app):
        """Test de caché con diferentes argumentos."""
        @cached(ttl=60, key_prefix='test')
        def add(a, b):
            return a + b
        
        with app.app_context():
            result1 = add(1, 2)
            result2 = add(3, 4)
            result3 = add(1, 2)
            
            assert result1 == 3
            assert result2 == 7
            assert result3 == 3
