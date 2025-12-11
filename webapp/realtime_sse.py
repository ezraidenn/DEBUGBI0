"""
Sistema de eventos en tiempo real usando Server-Sent Events (SSE).
Más eficiente que WebSockets para streaming unidireccional.
"""
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Generator, Dict, Any, Optional, List
from flask import Response, stream_with_context
import pytz

logger = logging.getLogger(__name__)


def fix_encoding(text: str) -> str:
    """Corrige problemas de encoding UTF-8 en textos de BioStar."""
    if not text:
        return text
    try:
        # Intenta corregir encoding mal interpretado (latin-1 -> utf-8)
        return text.encode('latin-1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text

# Importar EVENT_CODES y classify_event desde device_monitor
from src.api.device_monitor import EVENT_CODES

# Timezone de México
MEXICO_TZ = pytz.timezone('America/Mexico_City')

# Horario permitido para mostrar eventos (5:30 AM - 11:59 PM)
ALLOWED_START_HOUR = 5
ALLOWED_START_MINUTE = 30
ALLOWED_END_HOUR = 23
ALLOWED_END_MINUTE = 59


class RealtimeSSE:
    """Gestor de eventos en tiempo real usando SSE."""
    
    def __init__(self, monitor):
        """
        Inicializa el gestor de SSE.
        
        Args:
            monitor: Instancia de DeviceMonitor
        """
        self.monitor = monitor
        self.last_event_times = {}  # {device_id: last_datetime}
    
    def _classify_event(self, event_code):
        """Clasifica un evento según su código (misma lógica que app.py)."""
        if event_code in EVENT_CODES['ACCESS_GRANTED']:
            return 'success', 'Acceso Concedido'
        elif event_code in EVENT_CODES['ACCESS_DENIED']:
            return 'danger', 'Acceso Denegado'
        elif event_code in EVENT_CODES['FORCED_OPEN']:
            return 'warning', 'Puerta Forzada'
        elif event_code in EVENT_CODES['DOOR_LOCKED']:
            return 'info', 'Puerta Bloqueada'
        elif event_code in EVENT_CODES['DOOR_OPEN']:
            return 'primary', 'Puerta Abierta'
        elif event_code in EVENT_CODES['DOOR_CLOSE']:
            return 'secondary', 'Puerta Cerrada'
        else:
            return 'secondary', 'Otro Evento'
        
    def format_sse_message(self, data: Dict[str, Any], event: str = 'message') -> str:
        """
        Formatea un mensaje SSE.
        
        Args:
            data: Datos a enviar
            event: Tipo de evento
            
        Returns:
            Mensaje formateado para SSE
        """
        msg = f"event: {event}\n"
        msg += f"data: {json.dumps(data)}\n\n"
        return msg
    
    def _process_raw_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un evento RAW de la API a formato normalizado.
        
        Args:
            event: Evento RAW de BioStar API
            
        Returns:
            Evento procesado
        """
        # Extraer event_type_id
        event_type_id = event.get('event_type_id', {})
        event_code = event_type_id.get('code') if isinstance(event_type_id, dict) else None
        event_type = event_type_id.get('name', '') if isinstance(event_type_id, dict) else ''
        
        # Obtener y corregir encoding del nombre
        user_name = event.get('user_id', {}).get('name')
        user_name = fix_encoding(user_name) if user_name else user_name
        
        return {
            'id': event.get('id'),
            'datetime': event.get('datetime'),
            'server_datetime': event.get('server_datetime'),
            'device_id': event.get('device_id', {}).get('id'),
            'device_name': event.get('device_id', {}).get('name'),
            'event_code': event_code,
            'event_type': event_type,
            'user_id': event.get('user_id', {}).get('user_id'),
            'user_name': user_name,
            'door_id': event.get('door_id', [{}])[0].get('id') if event.get('door_id') else None,
            'door_name': event.get('door_id', [{}])[0].get('name') if event.get('door_id') else None,
        }
    
    def _get_event_code(self, event: Dict[str, Any]) -> str:
        """Extrae el código de evento de un evento RAW."""
        event_type = event.get('event_type_id')
        if isinstance(event_type, dict):
            return event_type.get('code', '')
        return str(event_type) if event_type else ''
    
    def _filter_events_by_time(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filtra eventos por horario permitido (5:30 AM - 11:59 PM hora México).
        IMPORTANTE: Evita mostrar eventos fuera del horario laboral.
        
        Args:
            events: Lista de eventos procesados
            
        Returns:
            Lista de eventos dentro del horario permitido
        """
        if not events:
            return []
        
        filtered = []
        today_local = datetime.now(MEXICO_TZ).date()
        
        start_minutes = ALLOWED_START_HOUR * 60 + ALLOWED_START_MINUTE
        end_minutes = ALLOWED_END_HOUR * 60 + ALLOWED_END_MINUTE
        
        for event in events:
            event_dt = event.get('datetime')
            if not event_dt:
                continue
            
            try:
                # Convertir a datetime si es string
                if isinstance(event_dt, str):
                    from dateutil import parser
                    event_dt = parser.parse(event_dt)
                
                if not isinstance(event_dt, datetime):
                    continue
                
                # Convertir a hora local de México
                if event_dt.tzinfo is None:
                    event_dt = pytz.utc.localize(event_dt)
                local_dt = event_dt.astimezone(MEXICO_TZ)
                
                # Verificar que sea del día actual
                if local_dt.date() != today_local:
                    continue
                
                # Verificar horario permitido
                event_minutes = local_dt.hour * 60 + local_dt.minute
                if start_minutes <= event_minutes <= end_minutes:
                    filtered.append(event)
                    
            except Exception as e:
                logger.debug(f"Error filtrando evento por tiempo: {e}")
                continue
        
        return filtered
    
    def _is_within_allowed_hours(self) -> bool:
        """
        Verifica si la hora actual está dentro del horario permitido.
        
        Returns:
            True si estamos en horario permitido (5:30 AM - 11:59 PM)
        """
        now = datetime.now(MEXICO_TZ)
        current_minutes = now.hour * 60 + now.minute
        start_minutes = ALLOWED_START_HOUR * 60 + ALLOWED_START_MINUTE
        end_minutes = ALLOWED_END_HOUR * 60 + ALLOWED_END_MINUTE
        return start_minutes <= current_minutes <= end_minutes
    
    def get_new_events(self, device_id: int, only_granted: bool = True) -> List[Dict[str, Any]]:
        """
        Obtiene eventos nuevos desde el último poll.
        
        Args:
            device_id: ID del dispositivo
            only_granted: Si True, solo retorna accesos concedidos
            
        Returns:
            Lista de eventos nuevos (procesados)
        """
        # Códigos de acceso concedido
        ACCESS_GRANTED_CODES = [
            '4097', '4098', '4099', '4100', '4101', '4102', '4103', '4104', '4105', '4106', '4107',
            '4112', '4113', '4114', '4115', '4118', '4119', '4120', '4121', '4122', '4123', '4128', '4129',
            '4865', '4866', '4867', '4868', '4869', '4870', '4871', '4872'
        ]
        
        try:
            # Obtener todos los eventos de hoy (RAW de la API)
            raw_events = self.monitor.get_device_events_today(device_id)
            
            # Filtrar solo accesos concedidos si se requiere
            if only_granted:
                raw_events = [e for e in raw_events if self._get_event_code(e) in ACCESS_GRANTED_CODES]
            
            # Procesar eventos RAW a formato normalizado
            all_events = [self._process_raw_event(e) for e in raw_events]
            
            if not all_events:
                logger.debug(f"No hay eventos para dispositivo {device_id}")
                return []
            
            # Si es la primera vez, guardar el último evento y retornar eventos recientes FILTRADOS
            if device_id not in self.last_event_times:
                # Ordenar por datetime descendente
                sorted_events = sorted(
                    all_events,
                    key=lambda x: x.get('datetime', datetime.min),
                    reverse=True
                )
                if sorted_events:
                    # Guardar el timestamp del evento más reciente
                    self.last_event_times[device_id] = sorted_events[0].get('datetime')
                    logger.info(f"Primera carga para dispositivo {device_id}: {len(sorted_events)} eventos totales")
                    
                    # CRÍTICO: Aplicar filtro de horario antes de enviar
                    # Esto evita enviar eventos de horario bloqueado (00:00-05:29)
                    filtered_events = self._filter_events_by_time(sorted_events[:10])
                    if filtered_events:
                        logger.info(f"Dispositivo {device_id}: {len(filtered_events)} eventos después de filtro horario")
                        return filtered_events[:5]  # Máximo 5 eventos iniciales
                    else:
                        logger.info(f"Dispositivo {device_id}: Sin eventos en horario permitido")
                        return []
                return []
            
            # Filtrar solo eventos más recientes que el último visto
            last_time = self.last_event_times[device_id]
            
            # Asegurar que ambos timestamps sean comparables
            new_events = []
            for event in all_events:
                event_time = event.get('datetime')
                if not event_time:
                    continue
                
                # Comparar timestamps (manejar timezone si es necesario)
                try:
                    if event_time > last_time:
                        new_events.append(event)
                except TypeError:
                    # Si hay problema de comparación, convertir a string y comparar
                    if str(event_time) > str(last_time):
                        new_events.append(event)
            
            # Actualizar el último tiempo si hay eventos nuevos
            if new_events:
                sorted_new = sorted(
                    new_events,
                    key=lambda x: x.get('datetime', datetime.min),
                    reverse=True
                )
                self.last_event_times[device_id] = sorted_new[0].get('datetime')
                logger.info(f"Dispositivo {device_id}: {len(new_events)} eventos nuevos detectados")
                
                # CRÍTICO: Aplicar filtro de horario a eventos nuevos
                filtered_new = self._filter_events_by_time(new_events)
                if len(filtered_new) != len(new_events):
                    logger.info(f"Dispositivo {device_id}: {len(new_events) - len(filtered_new)} eventos filtrados por horario")
                return filtered_new
            else:
                logger.debug(f"Dispositivo {device_id}: Sin eventos nuevos desde {last_time}")
            
            return []
            
        except Exception as e:
            logger.error(f"Error obteniendo eventos nuevos para dispositivo {device_id}: {e}", exc_info=True)
            return []
    
    def format_event_for_client(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formatea un evento para el cliente.
        
        Args:
            event: Evento original
            
        Returns:
            Evento formateado
        """
        # Convertir datetime a hora local
        event_time = event.get('datetime')
        time_str = 'N/A'
        datetime_full = None
        
        if event_time:
            try:
                # Si es string, convertir a datetime
                if isinstance(event_time, str):
                    # Intentar parsear ISO format
                    from dateutil import parser
                    event_time = parser.parse(event_time)
                
                # Si es datetime, procesar
                if isinstance(event_time, datetime):
                    # Asegurar timezone
                    if event_time.tzinfo is None:
                        event_time = pytz.utc.localize(event_time)
                    
                    # Convertir a hora local
                    local_time = event_time.astimezone(MEXICO_TZ)
                    time_str = local_time.strftime('%H:%M:%S')
                    datetime_full = local_time.isoformat()
            except Exception as e:
                logger.error(f"Error formateando datetime: {e}, valor: {event_time}")
                time_str = str(event_time) if event_time else 'N/A'
        
        # Clasificar evento usando la misma lógica que la tabla original
        event_code = event.get('event_code', '')
        badge_class, event_label = self._classify_event(event_code)
        
        return {
            'id': event.get('id', ''),
            'datetime': time_str,
            'datetime_full': datetime_full,
            'user': event.get('user_name'),  # Ya viene procesado
            'user_id': event.get('user_id'),  # Ya viene procesado
            'event_type': event.get('event_type', event_label),  # Usar label si no hay tipo
            'event_code': event_code,
            'device_id': event.get('device_id', ''),
            'door': event.get('door_name'),
            'badge_class': badge_class,  # success, danger, info, etc.
            'event_label': event_label,  # Acceso Concedido, Puerta Bloqueada, etc.
        }
    
    def stream_all_devices_events(
        self,
        device_ids: List[int],
        interval: int = 2
    ) -> Generator[str, None, None]:
        """
        Stream de eventos de MÚLTIPLES dispositivos (para dashboard).
        
        Args:
            device_ids: Lista de IDs de dispositivos
            interval: Intervalo de polling en segundos
            
        Yields:
            Mensajes SSE formateados
        """
        logger.info(f"Iniciando stream para {len(device_ids)} dispositivos")
        
        # Inicializar last_event_times para cada dispositivo
        for device_id in device_ids:
            if device_id not in self.last_event_times:
                self.last_event_times[device_id] = None
        
        last_heartbeat = time.time()
        heartbeat_interval = 16  # Heartbeat cada 16 segundos
        
        try:
            while True:
                # Obtener eventos nuevos de TODOS los dispositivos
                all_new_events = []
                
                for device_id in device_ids:
                    new_events = self.get_new_events(device_id)
                    
                    # Agregar device_id a cada evento para identificarlo
                    for event in new_events:
                        event['source_device_id'] = device_id
                        all_new_events.append(event)
                
                # Enviar eventos si hay nuevos
                if all_new_events:
                    logger.info(f"✅ Enviando {len(all_new_events)} eventos nuevos del dashboard")
                    
                    # Formatear eventos para el cliente
                    formatted_events = [
                        self.format_event_for_client(event)
                        for event in all_new_events
                    ]
                    
                    # Enviar como un solo mensaje con todos los eventos
                    yield self.format_sse_message({
                        'events': formatted_events,
                        'count': len(formatted_events)
                    }, event='new_events')
                
                # Enviar heartbeat si es necesario
                current_time = time.time()
                if current_time - last_heartbeat >= heartbeat_interval:
                    yield self.format_sse_message({'status': 'alive'}, event='heartbeat')
                    last_heartbeat = current_time
                
                # Esperar antes del siguiente poll
                time.sleep(interval)
                
        except GeneratorExit:
            logger.info("Cliente desconectado del stream del dashboard")
        except Exception as e:
            logger.error(f"Error en stream del dashboard: {e}")
            yield self.format_sse_message({'error': str(e)}, event='error')
    
    def stream_device_events(
        self,
        device_id: int,
        interval: int = 2
    ) -> Generator[str, None, None]:
        """
        Stream de eventos de un dispositivo.
        
        Args:
            device_id: ID del dispositivo
            interval: Intervalo de polling en segundos (default: 2)
            
        Yields:
            Mensajes SSE formateados
        """
        logger.info(f"🚀 Iniciando stream SSE para dispositivo {device_id} (intervalo: {interval}s)")
        
        # Enviar mensaje de conexión
        yield self.format_sse_message({
            'type': 'connected',
            'device_id': device_id,
            'timestamp': datetime.now(MEXICO_TZ).isoformat()
        }, event='connection')
        
        # Enviar heartbeat inicial
        yield self.format_sse_message({
            'type': 'heartbeat',
            'timestamp': datetime.now(MEXICO_TZ).isoformat()
        }, event='heartbeat')
        
        consecutive_errors = 0
        max_errors = 5
        poll_count = 0
        
        try:
            while True:
                try:
                    poll_count += 1
                    logger.debug(f"📡 Poll #{poll_count} para dispositivo {device_id}")
                    
                    # Obtener eventos nuevos
                    new_events = self.get_new_events(device_id)
                    
                    # Si hay eventos nuevos, enviarlos
                    if new_events:
                        logger.info(f"✅ Enviando {len(new_events)} eventos nuevos para dispositivo {device_id}")
                        
                        for event in new_events:
                            formatted_event = self.format_event_for_client(event)
                            logger.debug(f"📤 Evento: {formatted_event.get('user')} - {formatted_event.get('event_type')}")
                            yield self.format_sse_message(formatted_event, event='new_event')
                        
                        # Resetear contador de errores
                        consecutive_errors = 0
                    else:
                        logger.debug(f"⏸️ Sin eventos nuevos en poll #{poll_count}")
                    
                    # Enviar heartbeat cada 15 segundos (más frecuente para evitar timeout)
                    if poll_count % 8 == 0:  # Cada 8 polls (16 segundos con interval=2)
                        logger.debug("💓 Enviando heartbeat")
                        yield self.format_sse_message({
                            'type': 'heartbeat',
                            'timestamp': datetime.now(MEXICO_TZ).isoformat(),
                            'poll_count': poll_count
                        }, event='heartbeat')
                    
                    # Esperar antes de la siguiente consulta
                    time.sleep(interval)
                    
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"Error en stream SSE (intento {consecutive_errors}/{max_errors}): {e}")
                    
                    if consecutive_errors >= max_errors:
                        logger.error(f"Demasiados errores consecutivos, cerrando stream")
                        yield self.format_sse_message({
                            'type': 'error',
                            'message': 'Demasiados errores, reconectando...'
                        }, event='error')
                        break
                    
                    # Enviar mensaje de error pero continuar
                    yield self.format_sse_message({
                        'type': 'error',
                        'message': str(e)
                    }, event='error')
                    
                    time.sleep(interval * 2)  # Esperar más tiempo después de error
                    
        except GeneratorExit:
            logger.info(f"Cliente desconectado del stream para dispositivo {device_id}")
        except Exception as e:
            logger.error(f"Error fatal en stream SSE: {e}")
            yield self.format_sse_message({
                'type': 'error',
                'message': 'Error fatal en el servidor'
            }, event='error')
    
    def stream_all_devices(self, interval: int = 3) -> Generator[str, None, None]:
        """
        Stream de eventos de todos los dispositivos.
        
        Args:
            interval: Intervalo de polling en segundos (default: 3)
            
        Yields:
            Mensajes SSE formateados
        """
        logger.info("Iniciando stream SSE para todos los dispositivos")
        
        # Enviar mensaje de conexión
        yield self.format_sse_message({
            'type': 'connected',
            'timestamp': datetime.now(MEXICO_TZ).isoformat()
        }, event='connection')
        
        # Contador para heartbeat confiable (cada ~15 segundos con interval=3)
        poll_count = 0
        heartbeat_every = max(5, 15 // interval)  # Heartbeat cada ~15 segundos
        
        try:
            while True:
                try:
                    poll_count += 1
                    
                    # Obtener todos los dispositivos
                    devices = self.monitor.get_all_devices()
                    
                    # Revisar cada dispositivo
                    for device in devices:
                        device_id = device.get('id')
                        if not device_id:
                            continue
                        
                        # Obtener eventos nuevos (ya filtrados por horario)
                        new_events = self.get_new_events(device_id)
                        
                        # Enviar eventos nuevos
                        if new_events:
                            for event in new_events:
                                formatted_event = self.format_event_for_client(event)
                                formatted_event['device_name'] = device.get('name', 'Desconocido')
                                formatted_event['device_alias'] = device.get('alias')
                                yield self.format_sse_message(formatted_event, event='new_event')
                    
                    # Heartbeat confiable basado en contador (no en time() % N)
                    if poll_count % heartbeat_every == 0:
                        yield self.format_sse_message({
                            'type': 'heartbeat',
                            'timestamp': datetime.now(MEXICO_TZ).isoformat(),
                            'poll_count': poll_count
                        }, event='heartbeat')
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Error en stream SSE global: {e}")
                    yield self.format_sse_message({
                        'type': 'error',
                        'message': str(e)
                    }, event='error')
                    time.sleep(interval * 2)
                    
        except GeneratorExit:
            logger.info("Cliente desconectado del stream global")


def create_sse_response(generator: Generator) -> Response:
    """
    Crea una respuesta Flask SSE.
    
    Args:
        generator: Generador de mensajes SSE
        
    Returns:
        Response de Flask configurada para SSE
    """
    return Response(
        stream_with_context(generator),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # Deshabilitar buffering en nginx
            'Connection': 'keep-alive',
        }
    )
