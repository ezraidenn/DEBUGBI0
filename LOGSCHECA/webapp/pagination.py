"""
Sistema de paginación para tablas grandes.
"""
from typing import List, Dict, Any
from math import ceil


class Paginator:
    """Clase para manejar paginación de resultados."""
    
    def __init__(self, items: List[Any], page: int = 1, per_page: int = 50):
        """
        Inicializa el paginador.
        
        Args:
            items: Lista de items a paginar
            page: Número de página actual (1-indexed)
            per_page: Items por página
        """
        self.items = items
        self.total_items = len(items)
        self.per_page = per_page
        self.page = max(1, page)  # Asegurar que page >= 1
        self.total_pages = ceil(self.total_items / per_page) if per_page > 0 else 1
        
        # Ajustar página si excede el total
        if self.page > self.total_pages and self.total_pages > 0:
            self.page = self.total_pages
    
    @property
    def items_on_page(self) -> List[Any]:
        """Retorna los items de la página actual."""
        start = (self.page - 1) * self.per_page
        end = start + self.per_page
        return self.items[start:end]
    
    @property
    def has_prev(self) -> bool:
        """Verifica si hay página anterior."""
        return self.page > 1
    
    @property
    def has_next(self) -> bool:
        """Verifica si hay página siguiente."""
        return self.page < self.total_pages
    
    @property
    def prev_page(self) -> int:
        """Número de página anterior."""
        return self.page - 1 if self.has_prev else None
    
    @property
    def next_page(self) -> int:
        """Número de página siguiente."""
        return self.page + 1 if self.has_next else None
    
    def get_page_range(self, window: int = 5) -> List[int]:
        """
        Obtiene el rango de páginas a mostrar.
        
        Args:
            window: Número de páginas a mostrar alrededor de la actual
        
        Returns:
            Lista de números de página
        """
        if self.total_pages <= window:
            return list(range(1, self.total_pages + 1))
        
        # Calcular inicio y fin de la ventana
        half_window = window // 2
        start = max(1, self.page - half_window)
        end = min(self.total_pages, self.page + half_window)
        
        # Ajustar si estamos cerca del inicio o fin
        if self.page <= half_window:
            end = min(window, self.total_pages)
        elif self.page >= self.total_pages - half_window:
            start = max(1, self.total_pages - window + 1)
        
        return list(range(start, end + 1))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el paginador a diccionario."""
        return {
            'page': self.page,
            'per_page': self.per_page,
            'total_items': self.total_items,
            'total_pages': self.total_pages,
            'has_prev': self.has_prev,
            'has_next': self.has_next,
            'prev_page': self.prev_page,
            'next_page': self.next_page,
            'page_range': self.get_page_range(),
            'items': self.items_on_page
        }


def paginate_list(items: List[Any], page: int = 1, per_page: int = 50) -> Dict[str, Any]:
    """
    Función helper para paginar una lista.
    
    Args:
        items: Lista de items
        page: Número de página
        per_page: Items por página
    
    Returns:
        Diccionario con datos de paginación
    """
    paginator = Paginator(items, page, per_page)
    return paginator.to_dict()
