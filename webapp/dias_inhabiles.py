"""
Calendario de Días Inhábiles Oficiales de México
Incluye días festivos oficiales según la Ley Federal del Trabajo
"""

from datetime import date

# Días inhábiles oficiales de México para 2026
DIAS_INHABILES_2026 = [
    # Año Nuevo
    date(2026, 1, 1),
    
    # Día de la Constitución (primer lunes de febrero)
    date(2026, 2, 2),
    
    # Natalicio de Benito Juárez (tercer lunes de marzo)
    date(2026, 3, 16),
    
    # Jueves Santo (variable)
    date(2026, 4, 2),
    
    # Viernes Santo (variable)
    date(2026, 4, 3),
    
    # Día del Trabajo
    date(2026, 5, 1),
    
    # Día de la Independencia
    date(2026, 9, 16),
    
    # Revolución Mexicana (tercer lunes de noviembre)
    date(2026, 11, 16),
    
    # Transmisión del Poder Ejecutivo Federal (cada 6 años)
    # date(2024, 10, 1),  # Solo en años de cambio de gobierno
    
    # Navidad
    date(2026, 12, 25),
]

# Días inhábiles oficiales de México para 2027
DIAS_INHABILES_2027 = [
    # Año Nuevo
    date(2027, 1, 1),
    
    # Día de la Constitución (primer lunes de febrero)
    date(2027, 2, 1),
    
    # Natalicio de Benito Juárez (tercer lunes de marzo)
    date(2027, 3, 15),
    
    # Jueves Santo (variable)
    date(2027, 3, 25),
    
    # Viernes Santo (variable)
    date(2027, 3, 26),
    
    # Día del Trabajo
    date(2027, 5, 1),
    
    # Día de la Independencia
    date(2027, 9, 16),
    
    # Revolución Mexicana (tercer lunes de noviembre)
    date(2027, 11, 15),
    
    # Navidad
    date(2027, 12, 25),
]

# Días inhábiles oficiales de México para 2025
DIAS_INHABILES_2025 = [
    # Año Nuevo
    date(2025, 1, 1),
    
    # Día de la Constitución (primer lunes de febrero)
    date(2025, 2, 3),
    
    # Natalicio de Benito Juárez (tercer lunes de marzo)
    date(2025, 3, 17),
    
    # Jueves Santo (variable)
    date(2025, 4, 17),
    
    # Viernes Santo (variable)
    date(2025, 4, 18),
    
    # Día del Trabajo
    date(2025, 5, 1),
    
    # Día de la Independencia
    date(2025, 9, 16),
    
    # Revolución Mexicana (tercer lunes de noviembre)
    date(2025, 11, 17),
    
    # Navidad
    date(2025, 12, 25),
]

# Diccionario completo por año
DIAS_INHABILES_POR_ANIO = {
    2025: DIAS_INHABILES_2025,
    2026: DIAS_INHABILES_2026,
    2027: DIAS_INHABILES_2027,
}

def obtener_dias_inhabiles(anio):
    """
    Obtiene la lista de días inhábiles oficiales para un año específico.
    
    Args:
        anio (int): Año para el cual se requieren los días inhábiles
        
    Returns:
        list: Lista de objetos date con los días inhábiles oficiales
    """
    return DIAS_INHABILES_POR_ANIO.get(anio, [])

def es_dia_inhabil(fecha):
    """
    Verifica si una fecha es día inhábil oficial.
    
    Args:
        fecha (date): Fecha a verificar
        
    Returns:
        bool: True si es día inhábil oficial, False en caso contrario
    """
    dias_inhabiles = obtener_dias_inhabiles(fecha.year)
    return fecha in dias_inhabiles

def obtener_nombre_dia_inhabil(fecha):
    """
    Obtiene el nombre del día inhábil si aplica.
    
    Args:
        fecha (date): Fecha a verificar
        
    Returns:
        str: Nombre del día inhábil o None si no es inhábil
    """
    if not es_dia_inhabil(fecha):
        return None
    
    nombres = {
        (1, 1): "Año Nuevo",
        (2, 2): "Día de la Constitución",
        (2, 3): "Día de la Constitución",
        (2, 1): "Día de la Constitución",
        (3, 15): "Natalicio de Benito Juárez",
        (3, 16): "Natalicio de Benito Juárez",
        (3, 17): "Natalicio de Benito Juárez",
        (3, 25): "Jueves Santo",
        (3, 26): "Viernes Santo",
        (4, 2): "Jueves Santo",
        (4, 3): "Viernes Santo",
        (4, 17): "Jueves Santo",
        (4, 18): "Viernes Santo",
        (5, 1): "Día del Trabajo",
        (9, 16): "Día de la Independencia",
        (11, 15): "Revolución Mexicana",
        (11, 16): "Revolución Mexicana",
        (11, 17): "Revolución Mexicana",
        (12, 25): "Navidad",
    }
    
    return nombres.get((fecha.month, fecha.day), "Día Inhábil Oficial")
