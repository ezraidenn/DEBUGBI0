"""
Servicio de monitoreo en tiempo real para eventos de BioStar.
Detecta nuevos eventos y los transmite vía WebSocket.
OPTIMIZADO: Solo busca eventos nuevos desde el último timestamp.
"""
import threading
import time
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Set, List, Optional
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RealtimeMonitor:
    """Monitor de eventos en tiempo real OPTIMIZADO."""
    
    def __init__(self, socketio, device_monitor):
        """
        Inicializa el monitor en tiempo real.
        
        Args:
            socketio: Instancia de SocketIO
            device_monitor: Función para obtener DeviceMonitor
        """
        self.socketio = socketio
        self.get_monitor = device_monitor
        self.monitoring_devices: Set[int] = set()
        self.last_event_timestamp: Dict[int, datetime] = {}  # Último timestamp por dispositivo
        self.is_running = False
        self.thread = None
        self.monitor_instance = None  # Reutilizar instancia de monitor
        self.last_login = None  # Timestamp del último login
        
    def start(self):
        """Inicia el monitoreo en tiempo real."""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            logger.info("[OK] Monitor en tiempo real iniciado")
    
    def stop(self):
        """Detiene el monitoreo."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("[STOPPED] Monitor en tiempo real detenido")
    
    def add_device(self, device_id: int):
        """Agrega un dispositivo para monitorear."""
        self.monitoring_devices.add(device_id)
        logger.info(f"[ADDED] Monitoreando dispositivo {device_id}")
    
    def remove_device(self, device_id: int):
        """Remueve un dispositivo del monitoreo."""
        self.monitoring_devices.discard(device_id)
        if device_id in self.last_event_timestamp:
            del self.last_event_timestamp[device_id]
        logger.info(f"[REMOVED] Dejó de monitorear dispositivo {device_id}")
    
    def _get_or_create_monitor(self) -> Optional[object]:
        """Obtiene o crea una instancia de monitor (reutiliza para evitar logins constantes)."""
        # Reautenticar cada 5 minutos
        now = datetime.now()
        if self.monitor_instance is None or (self.last_login and (now - self.last_login).seconds > 300):
            self.monitor_instance = self.get_monitor()
            if self.monitor_instance:
                self.last_login = now
                logger.info("[OK] Monitor autenticado/reautenticado")
        return self.monitor_instance
    
    def _monitor_loop(self):
        """Loop principal de monitoreo."""
        logger.info("[STARTED] Loop de monitoreo iniciado")
        
        while self.is_running:
            try:
                if self.monitoring_devices:
                    self._check_for_new_events()
                time.sleep(2)  # Revisar cada 2 segundos
            except Exception as e:
                logger.error(f"Error en loop de monitoreo: {str(e)}")
                time.sleep(5)
    
    def _check_for_new_events(self):
        """Revisa si hay nuevos eventos OPTIMIZADO - solo desde último timestamp."""
        try:
            # Reutilizar monitor (no crear uno nuevo cada vez)
            monitor = self._get_or_create_monitor()
            if not monitor:
                return
            
            for device_id in list(self.monitoring_devices):
                try:
                    # Primera vez: obtener timestamp del último evento
                    if device_id not in self.last_event_timestamp:
                        # Solo obtener los últimos 10 eventos para inicializar
                        now = datetime.now()
                        start = now - timedelta(minutes=5)
                        events = monitor.get_device_events(device_id, start, now, limit=10)
                        
                        if events:
                            # Guardar timestamp del evento más reciente
                            latest = max(events, key=lambda e: e.get('datetime', datetime.min))
                            self.last_event_timestamp[device_id] = latest.get('datetime', now)
                            logger.info(f"[OK] Inicializado dispositivo {device_id} - Ultimo evento: {self.last_event_timestamp[device_id]}")
                        else:
                            self.last_event_timestamp[device_id] = now
                            logger.info(f"[OK] Inicializado dispositivo {device_id} - Sin eventos recientes")
                        continue
                    
                    # OPTIMIZACIÓN: Solo buscar eventos DESPUÉS del último timestamp
                    last_check = self.last_event_timestamp[device_id]
                    now = datetime.now()
                    
                    # Buscar solo eventos nuevos (desde último timestamp + 1 segundo)
                    start_time = last_check + timedelta(seconds=1)
                    
                    # Solo buscar si han pasado al menos 2 segundos
                    if (now - last_check).seconds < 2:
                        continue
                    
                    events = monitor.get_device_events(
                        device_id=device_id,
                        start_date=start_time,
                        end_date=now,
                        limit=50  # Máximo 50 eventos nuevos
                    )
                    
                    if events:
                        logger.info(f"🔔 {len(events)} nuevos eventos en dispositivo {device_id}")
                        self._emit_new_events(device_id, events)
                        
                        # Actualizar timestamp al más reciente
                        latest = max(events, key=lambda e: e.get('datetime', datetime.min))
                        self.last_event_timestamp[device_id] = latest.get('datetime', now)
                    
                except Exception as e:
                    logger.error(f"Error al revisar dispositivo {device_id}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error general en _check_for_new_events: {str(e)}")
    
    def _emit_new_events(self, device_id: int, events: List):
        """Emite nuevos eventos vía WebSocket."""
        for event in events:
            # Convertir datetime a string si es necesario
            event_datetime = event.get('datetime')
            if hasattr(event_datetime, 'isoformat'):
                event_datetime = event_datetime.isoformat()
            elif hasattr(event_datetime, 'strftime'):
                event_datetime = event_datetime.strftime('%Y-%m-%d %H:%M:%S')
            
            event_data = {
                'device_id': device_id,
                'event_id': event.get('id'),
                'datetime': event_datetime,
                'event_code': str(event.get('event_type_id', {}).get('code', '')),
                'event_type': event.get('event_type_id', {}).get('name', 'Evento'),
                'user_id': event.get('user_id', {}).get('user_id'),
                'user_name': event.get('user_id', {}).get('name', 'Desconocido'),
                'device_name': event.get('device_id', {}).get('name', ''),
            }
            
            # Emitir a todos los clientes conectados
            try:
                self.socketio.emit('new_event', event_data, namespace='/realtime')
                # PII (user_name) NO debe loggearse en produccion. Solo en dev con hash corto para correlacion.
                if os.environ.get('FLASK_ENV') == 'development':
                    user_name_raw = event_data.get('user_name') or ''
                    user_hash = hashlib.sha256(user_name_raw.encode('utf-8', errors='ignore')).hexdigest()[:8]
                    logger.debug(f"Evento emitido: Dispositivo {device_id}, UsuarioHash: {user_hash}, Tipo: {event_data['event_type']}")
            except Exception as e:
                logger.error(f"Error al emitir evento: {str(e)}")
