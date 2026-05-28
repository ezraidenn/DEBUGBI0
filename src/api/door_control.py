"""
Control de puertas para BioStar 2 API.
Funciones para activar/desactivar modo pánico.
"""
from src.api.biostar_client import _get_tls_verify
from src.api.device_monitor import DeviceMonitor
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def biostar_unlock_door(device_id: str, activate_alarm: bool = False) -> tuple[bool, str]:
    """
    Desbloquea una puerta permanentemente (MODO PÁNICO ACTIVADO).
    Opcionalmente activa la alarma de sonido del dispositivo.
    
    Args:
        device_id: ID del dispositivo BioStar
        activate_alarm: Si True, activa la alarma de sonido
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        monitor = DeviceMonitor(Config())
        if not monitor.login():
            return False, "Error de autenticación con BioStar"
        
        url = f"{monitor.client.host}/api/actions"
        headers = {
            "bs-session-id": monitor.client.token,
            "Content-Type": "application/json"
        }
        
        # Preparar acciones: siempre desbloquear, opcionalmente alarma
        actions = [
            {
                "device_id": {"id": str(device_id)},
                "action_type": "unlock_door"
            }
        ]
        
        if activate_alarm:
            actions.append({
                "device_id": {"id": str(device_id)},
                "action_type": "trigger_alarm"
            })
        
        payload = {
            "DeviceCollection": {
                "rows": actions
            }
        }
        
        logger.info(f"🔓 Desbloqueando puerta del dispositivo {device_id} (alarma: {activate_alarm})")
        
        response = monitor.client.session.post(
            url,
            json=payload,
            headers=headers,
            verify=_get_tls_verify(),
            timeout=10
        )
        
        if response.status_code == 200:
            msg = "Puerta desbloqueada"
            if activate_alarm:
                msg += " y alarma activada"
            logger.info(f"✅ {msg}: {device_id}")
            return True, msg + " exitosamente"
        elif response.status_code == 403:
            logger.error(f"❌ Permiso denegado para desbloquear puerta: {device_id}")
            return False, "Permiso denegado. Verifica los permisos del usuario en BioStar."
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('Response', {}).get('message', f'Error {response.status_code}')
            logger.error(f"❌ Error al desbloquear puerta {device_id}: {error_msg}")
            return False, error_msg
            
    except Exception as e:
        logger.error(f"❌ Excepción al desbloquear puerta {device_id}: {str(e)}")
        return False, f"Error de conexión: {str(e)}"


def biostar_lock_door(device_id: str, deactivate_alarm: bool = False) -> tuple[bool, str]:
    """
    Bloquea una puerta (MODO PÁNICO DESACTIVADO - volver a normalidad).
    Opcionalmente desactiva la alarma de sonido del dispositivo.
    
    Args:
        device_id: ID del dispositivo BioStar
        deactivate_alarm: Si True, desactiva la alarma de sonido
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        monitor = DeviceMonitor(Config())
        if not monitor.login():
            return False, "Error de autenticación con BioStar"
        
        url = f"{monitor.client.host}/api/actions"
        headers = {
            "bs-session-id": monitor.client.token,
            "Content-Type": "application/json"
        }
        
        # Preparar acciones: siempre bloquear, opcionalmente desactivar alarma
        actions = [
            {
                "device_id": {"id": str(device_id)},
                "action_type": "lock_door"
            }
        ]
        
        if deactivate_alarm:
            actions.append({
                "device_id": {"id": str(device_id)},
                "action_type": "release_alarm"
            })
        
        payload = {
            "DeviceCollection": {
                "rows": actions
            }
        }
        
        logger.info(f"🔒 Bloqueando puerta del dispositivo {device_id} (desactivar alarma: {deactivate_alarm})")
        
        response = monitor.client.session.post(
            url,
            json=payload,
            headers=headers,
            verify=_get_tls_verify(),
            timeout=10
        )
        
        if response.status_code == 200:
            msg = "Puerta bloqueada"
            if deactivate_alarm:
                msg += " y alarma desactivada"
            logger.info(f"✅ {msg}: {device_id}")
            return True, msg + " exitosamente"
        elif response.status_code == 403:
            logger.error(f"❌ Permiso denegado para bloquear puerta: {device_id}")
            return False, "Permiso denegado. Verifica los permisos del usuario en BioStar."
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('Response', {}).get('message', f'Error {response.status_code}')
            logger.error(f"❌ Error al bloquear puerta {device_id}: {error_msg}")
            return False, error_msg
            
    except Exception as e:
        logger.error(f"❌ Excepción al bloquear puerta {device_id}: {str(e)}")
        return False, f"Error de conexión: {str(e)}"


def biostar_open_door_temporary(device_id: str) -> tuple[bool, str]:
    """
    Abre una puerta temporalmente (3-5 segundos).
    Útil para pruebas o acceso puntual.
    
    Args:
        device_id: ID del dispositivo BioStar
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        monitor = DeviceMonitor(Config())
        if not monitor.login():
            return False, "Error de autenticación con BioStar"
        
        url = f"{monitor.client.host}/api/actions"
        headers = {
            "bs-session-id": monitor.client.token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "DeviceCollection": {
                "rows": [
                    {
                        "device_id": {"id": str(device_id)},
                        "action_type": "open_door"
                    }
                ]
            }
        }
        
        logger.info(f"🚪 Abriendo puerta temporalmente: {device_id}")
        
        response = monitor.client.session.post(
            url,
            json=payload,
            headers=headers,
            verify=_get_tls_verify(),
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Puerta abierta temporalmente: {device_id}")
            return True, "Puerta abierta temporalmente"
        elif response.status_code == 403:
            logger.error(f"❌ Permiso denegado para abrir puerta: {device_id}")
            return False, "Permiso denegado. Verifica los permisos del usuario en BioStar."
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('Response', {}).get('message', f'Error {response.status_code}')
            logger.error(f"❌ Error al abrir puerta {device_id}: {error_msg}")
            return False, error_msg
            
    except Exception as e:
        logger.error(f"❌ Excepción al abrir puerta {device_id}: {str(e)}")
        return False, f"Error de conexión: {str(e)}"
