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
    
    def get_all_users(self, limit: int = 1000) -> List[Dict]:
        """
        Obtiene la lista de todos los usuarios de BioStar.
        
        Args:
            limit: Cantidad máxima de usuarios a obtener
            
        Returns:
            Lista de usuarios con sus IDs y nombres
        """
        if not self.token:
            logger.error("No hay token de sesión. Ejecuta login() primero.")
            return []
        
        url = f"{self.host}/api/users"
        headers = {"bs-session-id": self.token}
        params = {"limit": limit}
        
        try:
            response = self.session.get(url, headers=headers, params=params, verify=False, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('UserCollection', {}).get('rows', [])
                logger.info(f"✓ {len(users)} usuarios encontrados")
                return users
            else:
                logger.error(f"✗ Error al obtener usuarios: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"✗ Error al obtener usuarios: {str(e)}")
            return []
    
    def search_users(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Busca usuarios por nombre o ID.
        
        Args:
            query: Texto a buscar
            limit: Cantidad máxima de resultados
            
        Returns:
            Lista de usuarios que coinciden con la búsqueda
        """
        if not self.token:
            logger.error("No hay token de sesión. Ejecuta login() primero.")
            return []
        
        url = f"{self.host}/api/users/search"
        headers = {
            "bs-session-id": self.token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "Query": {
                "limit": limit,
                "conditions": [
                    {
                        "column": "name",
                        "operator": 4,  # CONTAINS
                        "values": [query]
                    }
                ]
            }
        }
        
        try:
            response = self.session.post(url, json=payload, headers=headers, verify=False, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('UserCollection', {}).get('rows', [])
                logger.info(f"✓ {len(users)} usuarios encontrados para '{query}'")
                return users
            else:
                logger.error(f"✗ Error al buscar usuarios: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"✗ Error al buscar usuarios: {str(e)}")
            return []
    
    # ==================== CONTROL DE PUERTAS ====================
    
    def get_all_doors(self) -> List[Dict]:
        """
        Obtiene la lista de todas las puertas configuradas.
        
        Returns:
            Lista de puertas con sus IDs y configuración
        """
        if not self.token:
            logger.error("No hay token de sesión. Ejecuta login() primero.")
            return []
        
        url = f"{self.host}/api/doors"
        headers = {"bs-session-id": self.token}
        
        try:
            response = self.session.get(url, headers=headers, verify=False, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                doors = data.get('DoorCollection', {}).get('rows', [])
                logger.info(f"✓ {len(doors)} puertas encontradas")
                return doors
            else:
                logger.error(f"✗ Error al obtener puertas: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"✗ Error al obtener puertas: {str(e)}")
            return []
    
    def get_door_id_for_device(self, device_id: int) -> int:
        """
        Obtiene el ID de la puerta asociada a un dispositivo.
        
        Args:
            device_id: ID del dispositivo
            
        Returns:
            ID de la puerta asociada, o None si no se encuentra
        """
        doors = self.get_all_doors()
        device_id_str = str(device_id)
        
        for door in doors:
            # Buscar en entry_device_id
            entry_device = door.get('entry_device_id', {})
            if isinstance(entry_device, dict) and entry_device.get('id') == device_id_str:
                door_id = door.get('id')
                logger.info(f"✓ Dispositivo {device_id} -> Puerta {door_id} ({door.get('name')})")
                return int(door_id)
            
            # Buscar también en exit_device_id si existe
            exit_device = door.get('exit_device_id', {})
            if isinstance(exit_device, dict) and exit_device.get('id') == device_id_str:
                door_id = door.get('id')
                logger.info(f"✓ Dispositivo {device_id} -> Puerta {door_id} ({door.get('name')}) [exit]")
                return int(door_id)
        
        logger.warning(f"⚠ No se encontró puerta para dispositivo {device_id}")
        return None
    
    def open_door_by_device(self, device_id: int) -> bool:
        """
        Abre la puerta asociada a un dispositivo (temporal).
        
        Args:
            device_id: ID del dispositivo
            
        Returns:
            True si se abrió correctamente, False en caso contrario
        """
        door_id = self.get_door_id_for_device(device_id)
        if door_id:
            return self.open_door(door_id)
        return False
    
    def unlock_door_by_device(self, device_id: int) -> tuple:
        """
        Desbloquea permanentemente la puerta asociada a un dispositivo.
        La puerta permanece desbloqueada hasta que se llame release_door.
        
        Args:
            device_id: ID del dispositivo
            
        Returns:
            Tuple (success: bool, door_id: int or None)
        """
        door_id = self.get_door_id_for_device(device_id)
        if door_id:
            success = self.unlock_door(door_id)
            return (success, door_id if success else None)
        return (False, None)
    
    def release_door_by_device(self, device_id: int) -> bool:
        """
        Libera la puerta asociada a un dispositivo (vuelve a modo normal).
        
        Args:
            device_id: ID del dispositivo
            
        Returns:
            True si se liberó correctamente, False en caso contrario
        """
        door_id = self.get_door_id_for_device(device_id)
        if door_id:
            return self.release_door(door_id)
        return False
    
    def open_door(self, door_id: int) -> bool:
        """
        Abre una puerta específica (desbloqueo temporal).
        
        Args:
            door_id: ID de la puerta a abrir
            
        Returns:
            True si se abrió correctamente, False en caso contrario
        """
        if not self.token:
            logger.error("No hay token de sesión. Ejecuta login() primero.")
            return False
        
        # BioStar 2 API usa POST con body para control de puertas
        url = f"{self.host}/api/doors/open"
        headers = {
            "bs-session-id": self.token,
            "Content-Type": "application/json"
        }
        
        # El payload debe incluir la lista de IDs de puertas
        payload = {
            "DoorCollection": {
                "rows": [{"id": str(door_id)}]
            }
        }
        
        try:
            response = self.session.post(url, json=payload, headers=headers, verify=False, timeout=30)
            
            if response.status_code in [200, 204]:
                logger.info(f"✓ Puerta {door_id} abierta correctamente")
                return True
            else:
                logger.error(f"✗ Error al abrir puerta {door_id}: {response.status_code} - {response.text[:200]}")
                return False
        except Exception as e:
            logger.error(f"✗ Error al abrir puerta {door_id}: {str(e)}")
            return False
    
    def unlock_door(self, door_id: int) -> bool:
        """
        Desbloquea una puerta (permanece desbloqueada hasta lock/release).
        
        Args:
            door_id: ID de la puerta a desbloquear
            
        Returns:
            True si se desbloqueó correctamente, False en caso contrario
        """
        if not self.token:
            logger.error("No hay token de sesión. Ejecuta login() primero.")
            return False
        
        url = f"{self.host}/api/doors/unlock"
        headers = {
            "bs-session-id": self.token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "DoorCollection": {
                "rows": [{"id": str(door_id)}]
            }
        }
        
        try:
            response = self.session.post(url, json=payload, headers=headers, verify=False, timeout=30)
            
            if response.status_code in [200, 204]:
                logger.info(f"✓ Puerta {door_id} desbloqueada correctamente")
                return True
            else:
                logger.error(f"✗ Error al desbloquear puerta {door_id}: {response.status_code} - {response.text[:200]}")
                return False
        except Exception as e:
            logger.error(f"✗ Error al desbloquear puerta {door_id}: {str(e)}")
            return False
    
    def lock_door(self, door_id: int) -> bool:
        """
        Bloquea una puerta.
        
        Args:
            door_id: ID de la puerta a bloquear
            
        Returns:
            True si se bloqueó correctamente, False en caso contrario
        """
        if not self.token:
            logger.error("No hay token de sesión. Ejecuta login() primero.")
            return False
        
        url = f"{self.host}/api/doors/lock"
        headers = {
            "bs-session-id": self.token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "DoorCollection": {
                "rows": [{"id": str(door_id)}]
            }
        }
        
        try:
            response = self.session.post(url, json=payload, headers=headers, verify=False, timeout=30)
            
            if response.status_code in [200, 204]:
                logger.info(f"✓ Puerta {door_id} bloqueada correctamente")
                return True
            else:
                logger.error(f"✗ Error al bloquear puerta {door_id}: {response.status_code} - {response.text[:200]}")
                return False
        except Exception as e:
            logger.error(f"✗ Error al bloquear puerta {door_id}: {str(e)}")
            return False
    
    def release_door(self, door_id: int) -> bool:
        """
        Libera una puerta (vuelve a modo normal).
        
        Args:
            door_id: ID de la puerta a liberar
            
        Returns:
            True si se liberó correctamente, False en caso contrario
        """
        if not self.token:
            logger.error("No hay token de sesión. Ejecuta login() primero.")
            return False
        
        url = f"{self.host}/api/doors/release"
        headers = {
            "bs-session-id": self.token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "DoorCollection": {
                "rows": [{"id": str(door_id)}]
            }
        }
        
        try:
            response = self.session.post(url, json=payload, headers=headers, verify=False, timeout=30)
            
            if response.status_code in [200, 204]:
                logger.info(f"✓ Puerta {door_id} liberada correctamente")
                return True
            else:
                logger.error(f"✗ Error al liberar puerta {door_id}: {response.status_code} - {response.text[:200]}")
                return False
        except Exception as e:
            logger.error(f"✗ Error al liberar puerta {door_id}: {str(e)}")
            return False
    
    def trigger_alarm(self, device_id: int) -> bool:
        """
        Intenta activar la alarma en un dispositivo.
        
        NOTA: La API REST de BioStar 2 tiene soporte limitado para alarmas.
        Este método intenta varias alternativas pero puede no funcionar
        dependiendo de la configuración del servidor BioStar.
        
        Args:
            device_id: ID del dispositivo
            
        Returns:
            True si se activó correctamente, False en caso contrario
        """
        if not self.token:
            logger.error("No hay token de sesión. Ejecuta login() primero.")
            return False
        
        headers = {
            "bs-session-id": self.token,
            "Content-Type": "application/json"
        }
        
        # Intentar diferentes endpoints de alarma
        endpoints_to_try = [
            # Endpoint de fire alarm
            (f"{self.host}/api/fire_alarm/trigger", {"DeviceCollection": {"rows": [{"id": str(device_id)}]}}),
            # Endpoint de outputs/trigger
            (f"{self.host}/api/outputs/trigger", {"OutputCollection": {"rows": [{"device_id": {"id": str(device_id)}, "relay_index": "0"}]}}),
        ]
        
        for url, payload in endpoints_to_try:
            try:
                response = self.session.post(url, json=payload, headers=headers, verify=False, timeout=10)
                
                if response.status_code in [200, 204]:
                    logger.info(f"✓ Alarma activada en dispositivo {device_id} via {url}")
                    return True
            except Exception:
                continue
        
        # Si ningún endpoint funcionó, la API no soporta alarmas
        logger.warning(f"⚠ Alarmas no soportadas por API REST para dispositivo {device_id}")
        return False
    
    def trigger_alarm_by_door(self, door_id: int) -> bool:
        """
        Intenta activar alarma usando el ID de puerta.
        Alternativa que puede funcionar en algunas configuraciones.
        
        Args:
            door_id: ID de la puerta
            
        Returns:
            True si se activó, False en caso contrario
        """
        if not self.token:
            return False
        
        headers = {
            "bs-session-id": self.token,
            "Content-Type": "application/json"
        }
        
        # La API de BioStar no tiene un endpoint directo para alarmas de puerta
        # pero podemos intentar con clear_alarm (que sí funciona) para verificar conectividad
        # En una emergencia real, el desbloqueo de puerta es más importante que la alarma
        logger.info(f"ℹ Alarmas de puerta no soportadas directamente por API REST (door_id={door_id})")
        return False
