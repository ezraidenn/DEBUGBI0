"""
Utilidad para filtrar usuarios basándose en grupos excluidos.
"""
import os
from typing import List, Dict, Any


def get_excluded_groups() -> List[str]:
    """
    Obtiene la lista de grupos de usuarios a excluir desde variables de entorno.
    
    Returns:
        Lista de nombres de grupos a excluir
    """
    excluded = os.getenv('EXCLUDED_USER_GROUPS', '')
    if not excluded:
        return []
    
    # Separar por comas y limpiar espacios
    groups = [g.strip() for g in excluded.split(',') if g.strip()]
    return groups


def should_exclude_event(event: Dict) -> bool:
    """
    Determina si un evento debe ser excluido basándose en el grupo del usuario.
    
    ESTRUCTURA REAL DE BIOSTAR:
    event = {
        "user_group_id": {
            "id": "1594",
            "name": "Anthea"  // <- Nombre del grupo aquí
        },
        "user_id": {
            "user_id": "9663",
            "name": "col_10165"
        }
    }
    
    Args:
        event: Evento de BioStar
        
    Returns:
        True si el evento debe ser excluido, False en caso contrario
    """
    excluded_groups = get_excluded_groups()
    
    # Si no hay grupos excluidos, no filtrar nada
    if not excluded_groups:
        return False
    
    # Obtener el campo user_group_id del EVENTO (no de user_id)
    group_data = event.get('user_group_id', {})
    
    if isinstance(group_data, dict):
        group_name = group_data.get('name', '')
        if group_name:
            # Verificar si el nombre del grupo coincide con alguno excluido
            for excluded in excluded_groups:
                if excluded.lower() in group_name.lower():
                    return True
    
    return False


def filter_events(events: List[Dict]) -> List[Dict]:
    """
    Filtra una lista de eventos, excluyendo aquellos de usuarios en grupos excluidos.
    
    Args:
        events: Lista de eventos de BioStar
        
    Returns:
        Lista de eventos filtrados
    """
    excluded_groups = get_excluded_groups()
    
    # Si no hay grupos excluidos, retornar todos los eventos
    if not excluded_groups:
        return events
    
    original_count = len(events)
    filtered = []
    
    for event in events:
        if not should_exclude_event(event):
            filtered.append(event)
    
    filtered_count = original_count - len(filtered)
    if filtered_count > 0:
        print(f"🚫 Filtrados {filtered_count} eventos de grupos excluidos: {', '.join(excluded_groups)}")
    
    return filtered


def filter_users_list(users: List[Dict]) -> List[Dict]:
    """
    Filtra una lista de usuarios, excluyendo aquellos en grupos excluidos.
    
    Args:
        users: Lista de usuarios
        
    Returns:
        Lista de usuarios filtrados
    """
    excluded_groups = get_excluded_groups()
    
    # Si no hay grupos excluidos, retornar todos los usuarios
    if not excluded_groups:
        return users
    
    filtered = []
    for user in users:
        # Verificar tanto el campo 'name' como cualquier campo de grupo
        user_name = user.get('name', '')
        user_group = user.get('user_group', '') or user.get('group', '')
        
        should_exclude = False
        
        # Verificar nombre
        if user_name:
            for excluded in excluded_groups:
                if excluded.lower() in user_name.lower():
                    should_exclude = True
                    break
        
        # Verificar grupo
        if not should_exclude and user_group:
            for excluded in excluded_groups:
                if excluded.lower() in str(user_group).lower():
                    should_exclude = True
                    break
        
        if not should_exclude:
            filtered.append(user)
    
    return filtered
