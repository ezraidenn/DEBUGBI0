"""
Cliente básico para la API de BioStar 2.
"""
import requests
import urllib3
from typing import Dict, List, Optional

from src.utils.logger import get_logger

# Deshabilitar advertencias SSL para certificados autofirmados
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = get_logger(__name__)


class BioStarAPIClient:
    """Cliente para interactuar con la API de BioStar 2."""
    
    def __init__(self, host: str, username: str, password: str):
        """
        Inicializa el cliente de BioStar 2.
        
        Args:
            host: URL del servidor BioStar (ej: https://10.0.0.100)
            username: Usuario para autenticación
            password: Contraseña para autenticación
        """
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.session = requests.Session()
        self.session.verify = False  # Desactivar verificación SSL
    
    def login(self) -> bool:
        """
        Autentica contra el servidor BioStar 2.
        
        Returns:
            True si la autenticación fue exitosa, False en caso contrario
        """
        url = f"{self.host}/api/login"
        
        # BioStar 2 API requiere el formato con objeto "User"
        payload = {
            "User": {
                "login_id": self.username,
                "password": self.password
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"Autenticando en BioStar 2: {self.host}")
            response = self.session.post(url, json=payload, headers=headers, verify=False, timeout=30)
            
            if response.status_code == 200:
                # Extraer token del header
                self.token = response.headers.get('bs-session-id')
                
                if self.token:
                    # Agregar el token como cookie
                    self.session.cookies.set('bs-session-id', self.token, 
                                            domain=self.host.replace('https://', '').replace('http://', ''))
                    logger.info(f"✓ Autenticación exitosa. Token: {self.token[:20]}...")
                    return True
                else:
                    logger.error("Token no encontrado en la respuesta")
                    return False
            else:
                logger.error(f"Error de autenticación: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión al autenticar: {str(e)}")
            return False
    
    def get_event_types(self) -> List[Dict]:
        """
        Obtiene la lista de todos los tipos de evento configurados.
        
        Returns:
            Lista de tipos de evento con códigos y nombres
        """
        if not self.token:
            logger.error("No hay token de sesión. Ejecuta login() primero.")
            return []
        
        url = f"{self.host}/api/event_types"
        headers = {"bs-session-id": self.token}
        
        try:
            response = self.session.get(url, headers=headers, verify=False, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                event_types = data.get('EventTypeCollection', {}).get('rows', [])
                logger.info(f"✓ {len(event_types)} tipos de evento encontrados")
                return event_types
            else:
                logger.error(f"✗ Error al obtener tipos de evento: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"✗ Error: {str(e)}")
            return []
    
    def get_all_devices(self) -> List[Dict]:
        """
        Obtiene la lista de todos los dispositivos/lectores configurados.
        
        Returns:
            Lista de dispositivos con sus IDs y nombres
        """
        if not self.token:
            logger.error("No hay token de sesión. Ejecuta login() primero.")
            return []
        
        url = f"{self.host}/api/devices"
        headers = {"bs-session-id": self.token}
        
        try:
            response = self.session.get(url, headers=headers, verify=False, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                devices = data.get('DeviceCollection', {}).get('rows', [])
                logger.info(f"✓ {len(devices)} dispositivos encontrados")
                return devices
            else:
                logger.error(f"✗ Error al obtener dispositivos: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"✗ Error: {str(e)}")
            return []
    
    def get_device_by_id(self, device_id: int) -> Optional[Dict]:
        """
        Obtiene un dispositivo específico por ID usando el endpoint directo.
        
        Args:
            device_id: ID del dispositivo
            
        Returns:
            Información del dispositivo o None si no existe
        """
        if not self.token:
            logger.error("No hay token de sesión. Ejecuta login() primero.")
            return None
        
        url = f"{self.host}/api/devices/{device_id}"
        headers = {"bs-session-id": self.token}
        
        try:
            response = self.session.get(url, headers=headers, verify=False, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                device = data.get('Device', {})
                if device:
                    logger.info(f"✓ Dispositivo {device_id} encontrado: {device.get('name', 'Sin nombre')}")
                    return device
                else:
                    logger.warning(f"⚠ Dispositivo {device_id} no tiene datos")
                    return None
            elif response.status_code == 404:
                logger.warning(f"⚠ Dispositivo {device_id} no encontrado (404)")
                return None
            else:
                logger.error(f"✗ Error al obtener dispositivo {device_id}: {response.status_code}")
                logger.error(f"Response: {response.text[:200]}")
                return None
        except Exception as e:
            logger.error(f"✗ Error al obtener dispositivo {device_id}: {str(e)}")
            return None
    
    def search_events(self, conditions: List[Dict], limit: int = 1000, 
                     offset: int = 0, order_by: str = "datetime", 
                     descending: bool = True) -> List[Dict]:
        """
        Búsqueda genérica de eventos con filtros personalizados.
        
        Args:
            conditions: Lista de condiciones de filtrado
            limit: Cantidad máxima de registros (máx recomendado: 2000)
            offset: Offset para paginación
            order_by: Columna para ordenar
            descending: Orden descendente (True) o ascendente (False)
            
        Returns:
            Lista de eventos
        """
        if not self.token:
            logger.error("No hay token de sesión. Ejecuta login() primero.")
            return []
        
        url = f"{self.host}/api/events/search"
        
        headers = {
            "bs-session-id": self.token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "Query": {
                "limit": limit,
                "offset": offset,
                "conditions": conditions,
                "orders": [
                    {
                        "column": order_by,
                        "descending": descending
                    }
                ]
            }
        }
        
        try:
            response = self.session.post(url, json=payload, headers=headers, verify=False, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('EventCollection', {}).get('rows', [])
                logger.info(f"✓ {len(events)} eventos encontrados")
                return events
            else:
                logger.error(f"✗ Error al buscar eventos: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"✗ Error: {str(e)}")
            return []
    
    def get_event_types(self) -> List[Dict]:
        """
        Obtiene la lista de tipos de eventos disponibles.
        
        Returns:
            Lista de tipos de eventos con códigos y descripciones
        """
        if not self.token:
            logger.error("No hay token de sesión. Ejecuta login() primero.")
            return []
        
        url = f"{self.host}/api/event_types"
        headers = {"bs-session-id": self.token}
        
        try:
            response = self.session.get(url, headers=headers, verify=False, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                event_types = data.get('EventTypeCollection', {}).get('rows', [])
                logger.info(f"✓ {len(event_types)} tipos de eventos encontrados")
                return event_types
            else:
                logger.error(f"✗ Error al obtener tipos de eventos: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"✗ Error: {str(e)}")
            return []
