"""
Monitor especializado para dispositivos/checadores de BioStar 2.
Enfocado en debugging y obtención de logs diarios.
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import pytz

from src.api.biostar_client import BioStarAPIClient
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Timezone de México
MEXICO_TZ = pytz.timezone('America/Mexico_City')

# Códigos de eventos de BioStar 2
EVENT_CODES = {
    # Accesos exitosos (VERIFY_SUCCESS)
    'ACCESS_GRANTED': [
        '4097',   # VERIFY_SUCCESS_ID_PIN
        '4098',   # VERIFY_SUCCESS_ID_FINGERPRINT
        '4099',   # VERIFY_SUCCESS_ID_FINGERPRINT_PIN
        '4100',   # VERIFY_SUCCESS_ID_FACE
        '4101',   # VERIFY_SUCCESS_ID_FACE_PIN
        '4102',   # VERIFY_SUCCESS_CARD
        '4103',   # VERIFY_SUCCESS_CARD_PIN
        '4104',   # VERIFY_SUCCESS_CARD_FINGERPRINT
        '4105',   # VERIFY_SUCCESS_CARD_FINGERPRINT_PIN
        '4106',   # VERIFY_SUCCESS_CARD_FACE
        '4107',   # VERIFY_SUCCESS_CARD_FACE_PIN
        '4112',   # VERIFY_SUCCESS_CARD_FACE_FINGER
        '4113',   # VERIFY_SUCCESS_CARD_FINGER_FACE
        '4114',   # VERIFY_SUCCESS_ID_FACE_FINGER
        '4115',   # VERIFY_SUCCESS_ID_FINGER_FACE
        '4118',   # VERIFY_SUCCESS_MOBILE_CARD
        '4119',   # VERIFY_SUCCESS_MOBILE_CARD_PIN
        '4120',   # VERIFY_SUCCESS_MOBILE_CARD_FINGER
        '4121',   # VERIFY_SUCCESS_MOBILE_CARD_FINGER_PIN
        '4122',   # VERIFY_SUCCESS_MOBILE_CARD_FACE
        '4123',   # VERIFY_SUCCESS_MOBiLE_CARD_FACE_PIN
        '4128',   # VERIFY_SUCCESS_MOBILE_CARD_FACE_FINGER
        '4129',   # VERIFY_SUCCESS_MOBILE_CARD_FINGER_FACE
        # IDENTIFY_SUCCESS
        '4865',   # IDENTIFY_SUCCESS_FINGERPRINT
        '4866',   # IDENTIFY_SUCCESS_FINGERPRINT_PIN
        '4867',   # IDENTIFY_SUCCESS_FACE
        '4868',   # IDENTIFY_SUCCESS_FACE_PIN
        '4869',   # IDENTIFY_SUCCESS_FACE_FINGER
        '4870',   # IDENTIFY_SUCCESS_FACE_FINGER_PIN
        '4871',   # IDENTIFY_SUCCESS_FINGER_FACE
        '4872',   # IDENTIFY_SUCCESS_FINGER_FACE_PIN
    ],
    # Accesos denegados
    'ACCESS_DENIED': [
        '4353',   # VERIFY_FAIL_ID
        '4354',   # VERIFY_FAIL_CARD
        '4355',   # VERIFY_FAIL_PIN
        '4356',   # VERIFY_FAIL_FINGERPRINT
        '4357',   # VERIFY_FAIL_FACE
        '4360',   # VERIFY_FAIL_MOBILE_CARD
        '5123',   # IDENTIFY_FAIL_PIN
        '5124',   # IDENTIFY_FAIL_FINGERPRINT
        '5125',   # IDENTIFY_FAIL_FACE
        '6401',   # ACCESS_DENIED_ACCESS_GROUP
        '6402',   # ACCESS_DENIED_DISABLED
        '6403',   # ACCESS_DENIED_EXPIRED
        '6404',   # ACCESS_DENIED_ON_BLACKLIST
        '6405',   # ACCESS_DENIED_APB
        '6406',   # ACCESS_DENIED_TIMED_APB
        '6407',   # ACCESS_DENIED_FORCED_LOCK_SCHEDULE
        '6414',   # ACCESS_DENIED_INTRUSION_ALARM
        '6415',   # ACCESS_DENIED_INTERLOCK_ALARM
        '6418',   # ACCESS_DENIED_ANTI_TAILGATING_DEVICE
        '6419',   # ACCESS_DENIED_HIGH_TEMPERATURE
        '6420',   # ACCESS_DENIED_NONE_TEMPERATURE
        '6421',   # ACCESS_DENIED_UNMASK_DETECT
    ],
    # Puerta forzada
    'FORCED_OPEN': ['21504'],
    # Puerta abierta
    'DOOR_OPEN': ['20992'],
    # Puerta cerrada
    'DOOR_CLOSE': ['21248'],
    # Puerta bloqueada
    'DOOR_LOCKED': ['20736'],
}


class DeviceMonitor:
    """Monitor de dispositivos/checadores con funciones de debugging."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Inicializa el monitor de dispositivos.
        
        Args:
            config: Configuración (si no se provee, se crea una nueva)
        """
        self.config = config or Config()
        biostar_cfg = self.config.biostar_config
        
        self.client = BioStarAPIClient(
            host=biostar_cfg['host'],
            username=biostar_cfg['username'],
            password=biostar_cfg['password']
        )
        
        self.devices_cache = []
    
    def login(self) -> bool:
        """Autentica con BioStar."""
        return self.client.login()
    
    def get_all_devices(self, refresh: bool = False) -> List[Dict]:
        """
        Obtiene todos los dispositivos/checadores.
        
        Args:
            refresh: Si True, fuerza actualización del cache
            
        Returns:
            Lista de dispositivos con información completa
        """
        if not self.devices_cache or refresh:
            self.devices_cache = self.client.get_all_devices()
        
        # Enriquecer con aliases
        enriched_devices = []
        for device in self.devices_cache:
            device_copy = device.copy()
            device_id = str(device['id'])
            alias_info = self.config.get_device_alias(device_id)
            
            if alias_info:
                device_copy['alias'] = alias_info.get('alias', '')
                device_copy['location'] = alias_info.get('location', '')
                device_copy['notes'] = alias_info.get('notes', '')
            else:
                device_copy['alias'] = ''
                device_copy['location'] = ''
                device_copy['notes'] = ''
            
            enriched_devices.append(device_copy)
        
        return enriched_devices
    
    def get_device_by_id(self, device_id: int) -> Optional[Dict]:
        """
        Obtiene información de un dispositivo específico.
        
        Args:
            device_id: ID del dispositivo
            
        Returns:
            Información del dispositivo o None si no existe
        """
        # Try to get device directly from API first
        device = self.client.get_device_by_id(device_id)
        
        if device:
            # Enrich with alias info
            device_id_str = str(device['id'])
            alias_info = self.config.get_device_alias(device_id_str)
            
            if alias_info:
                device['alias'] = alias_info.get('alias', '')
                device['location'] = alias_info.get('location', '')
                device['notes'] = alias_info.get('notes', '')
            else:
                device['alias'] = ''
                device['location'] = ''
                device['notes'] = ''
            
            return device
        
        # Fallback: search in cached list
        devices = self.get_all_devices(refresh=True)
        for dev in devices:
            if dev['id'] == device_id:
                return dev
        
        return None
    
    def set_device_alias(self, device_id: int, alias: str, location: str = "", notes: str = ""):
        """
        Asigna un alias/nombre personalizado a un dispositivo.
        
        Args:
            device_id: ID del dispositivo
            alias: Nombre personalizado
            location: Ubicación del dispositivo
            notes: Notas adicionales
        """
        self.config.set_device_alias(str(device_id), alias, location, notes)
        logger.info(f"✓ Alias asignado al dispositivo {device_id}: '{alias}'")
    
    def _filter_events_by_time(self, events: List[Dict], start_hour: int = 5, 
                              start_minute: int = 30, end_hour: int = 23, 
                              end_minute: int = 59) -> List[Dict]:
        """
        Filtra eventos para mostrar solo los que ocurren entre start_time y end_time.
        Por defecto: 5:30 AM a 11:59 PM (hora local de México) del DÍA ACTUAL.
        
        Args:
            events: Lista de eventos
            start_hour: Hora de inicio (default: 5)
            start_minute: Minuto de inicio (default: 30)
            end_hour: Hora de fin (default: 23)
            end_minute: Minuto de fin (default: 59)
            
        Returns:
            Lista de eventos filtrados
        """
        filtered_events = []
        
        # Obtener fecha actual en hora local
        today_local = datetime.now(MEXICO_TZ).date()
        
        for event in events:
            event_dt = event.get('datetime')
            if event_dt is None:
                continue
            
            # Si es string, convertir a datetime
            if isinstance(event_dt, str):
                try:
                    from dateutil import parser
                    event_dt = parser.parse(event_dt)
                except:
                    continue
            
            # Si no es datetime, saltar
            if not isinstance(event_dt, datetime):
                continue
            
            # Convertir a hora local
            try:
                if event_dt.tzinfo is not None:
                    local_dt = event_dt.astimezone(MEXICO_TZ)
                else:
                    utc_dt = pytz.utc.localize(event_dt)
                    local_dt = utc_dt.astimezone(MEXICO_TZ)
            except:
                continue
            
            # Verificar que sea del día actual
            if local_dt.date() != today_local:
                continue
            
            # Obtener hora y minuto
            event_hour = local_dt.hour
            event_minute = local_dt.minute
            
            # Verificar si está dentro del rango
            event_time_minutes = event_hour * 60 + event_minute
            start_time_minutes = start_hour * 60 + start_minute
            end_time_minutes = end_hour * 60 + end_minute
            
            if start_time_minutes <= event_time_minutes <= end_time_minutes:
                filtered_events.append(event)
        
        return filtered_events
    
    def get_device_events_today(self, device_id: int) -> List[Dict]:
        """
        Obtiene todos los eventos del día actual de un dispositivo.
        
        Args:
            device_id: ID del dispositivo
            
        Returns:
            Lista de eventos del día
        """
        # Obtener rango del día actual
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        return self.get_device_events(device_id, today, tomorrow)
    
    def get_device_events(self, device_id: int, start_date: datetime, 
                         end_date: datetime, limit: int = 2000) -> List[Dict]:
        """
        Obtiene eventos de un dispositivo en un rango de fechas.
        
        Args:
            device_id: ID del dispositivo
            start_date: Fecha inicial
            end_date: Fecha final
            limit: Cantidad máxima de registros
            
        Returns:
            Lista de eventos
        """
        conditions = [
            {
                "column": "device_id.id",
                "operator": 0,  # Equal
                "values": [str(device_id)]
            },
            {
                "column": "datetime",
                "operator": 3,  # Between
                "values": [
                    start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                ]
            }
        ]
        
        logger.info(f"Obteniendo eventos del dispositivo {device_id}...")
        logger.info(f"  Rango: {start_date.strftime('%Y-%m-%d %H:%M')} - {end_date.strftime('%Y-%m-%d %H:%M')}")
        
        return self.client.search_events(conditions, limit=limit)
    
    def get_device_events_by_type(self, device_id: int, event_codes: List[str],
                                  start_date: datetime, end_date: datetime,
                                  limit: int = 2000) -> List[Dict]:
        """
        Obtiene eventos de un dispositivo filtrados por tipo.
        
        Args:
            device_id: ID del dispositivo
            event_codes: Lista de códigos de evento (ej: ["4864", "4865"])
            start_date: Fecha inicial
            end_date: Fecha final
            limit: Cantidad máxima de registros
            
        Returns:
            Lista de eventos filtrados
        """
        conditions = [
            {
                "column": "device_id.id",
                "operator": 0,
                "values": [str(device_id)]
            },
            {
                "column": "datetime",
                "operator": 3,
                "values": [
                    start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                ]
            },
            {
                "column": "event_type_id.code",
                "operator": 5,  # In
                "values": event_codes
            }
        ]
        
        logger.info(f"Obteniendo eventos tipo {event_codes} del dispositivo {device_id}...")
        return self.client.search_events(conditions, limit=limit)
    
    def events_to_dataframe(self, events: List[Dict]) -> pd.DataFrame:
        """
        Convierte eventos a DataFrame para análisis.
        
        Args:
            events: Lista de eventos de la API
            
        Returns:
            DataFrame con eventos normalizados
        """
        processed = []
        
        for event in events:
            record = {
                'id': event.get('id'),
                'datetime': event.get('datetime'),
                'server_datetime': event.get('server_datetime'),
                'device_id': event.get('device_id', {}).get('id'),
                'device_name': event.get('device_id', {}).get('name'),
                'event_code': event.get('event_type_id', {}).get('code'),
                'event_type': event.get('event_type_id', {}).get('name', ''),
                'user_id': event.get('user_id', {}).get('user_id'),
                'user_name': event.get('user_id', {}).get('name'),
                'door_id': event.get('door_id', [{}])[0].get('id') if event.get('door_id') else None,
                'door_name': event.get('door_id', [{}])[0].get('name') if event.get('door_id') else None,
            }
            processed.append(record)
        
        df = pd.DataFrame(processed)
        
        # Convertir fechas y remover timezone para Excel
        if not df.empty:
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_localize(None)
            if 'server_datetime' in df.columns:
                df['server_datetime'] = pd.to_datetime(df['server_datetime']).dt.tz_localize(None)
        
        return df
    
    def export_daily_debug(self, device_id: int, output_dir: str = "data/outputs") -> str:
        """
        Exporta debug completo del día de un dispositivo a Excel.
        
        Args:
            device_id: ID del dispositivo
            output_dir: Directorio de salida
            
        Returns:
            Path del archivo generado
        """
        # Obtener información del dispositivo
        device = self.get_device_by_id(device_id)
        device_name = device.get('alias') or device.get('name', f'Device_{device_id}') if device else f'Device_{device_id}'
        
        # Obtener eventos del día
        events = self.get_device_events_today(device_id)
        
        if not events:
            logger.warning(f"No hay eventos del día para el dispositivo {device_id}")
            return ""
        
        # Convertir a DataFrame
        df = self.events_to_dataframe(events)
        
        # Crear directorio de salida
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = device_name.replace(' ', '_').replace('/', '_')
        filename = output_path / f"debug_{safe_name}_{timestamp}.xlsx"
        
        # Exportar a Excel con formato
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Hoja principal con todos los eventos
            df.to_excel(writer, sheet_name='Eventos', index=False)
            
            # Hoja de resumen
            if not df.empty:
                # Calcular métricas con códigos correctos
                access_granted = 0
                access_denied = 0
                if 'event_code' in df.columns:
                    access_granted = len(df[df['event_code'].isin(EVENT_CODES['ACCESS_GRANTED'])])
                    access_denied = len(df[df['event_code'].isin(EVENT_CODES['ACCESS_DENIED'])])
                
                summary_data = {
                    'Métrica': [
                        'Total de eventos',
                        'Primer evento',
                        'Último evento',
                        'Accesos concedidos',
                        'Accesos denegados',
                        'Usuarios únicos'
                    ],
                    'Valor': [
                        len(df),
                        df['datetime'].min().strftime('%Y-%m-%d %H:%M:%S') if 'datetime' in df.columns else 'N/A',
                        df['datetime'].max().strftime('%Y-%m-%d %H:%M:%S') if 'datetime' in df.columns else 'N/A',
                        access_granted,
                        access_denied,
                        df['user_id'].nunique() if 'user_id' in df.columns else 0
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Resumen', index=False)
                
                # Hoja de eventos por tipo
                if 'event_type' in df.columns:
                    event_counts = df['event_type'].value_counts().reset_index()
                    event_counts.columns = ['Tipo de Evento', 'Cantidad']
                    event_counts.to_excel(writer, sheet_name='Por Tipo', index=False)
        
        logger.info(f"✓ Debug exportado a: {filename}")
        return str(filename)
    
    def get_debug_summary(self, device_id: int) -> Dict:
        """
        Obtiene un resumen rápido del debug del día.
        Filtra eventos entre 5:30 AM y 11:59 PM (hora local).
        
        Args:
            device_id: ID del dispositivo
            
        Returns:
            Diccionario con resumen de eventos
        """
        events = self.get_device_events_today(device_id)
        
        # Filtrar eventos por horario (5:30 AM - 11:59 PM hora local)
        events = self._filter_events_by_time(events)
        
        df = self.events_to_dataframe(events)
        
        if df.empty:
            return {
                'total_events': 0,
                'access_granted': 0,
                'access_denied': 0,
                'unique_users': 0,
                'first_event': None,
                'last_event': None
            }
        
        # Contar accesos concedidos (todos los códigos de ACCESS_GRANTED)
        access_granted = 0
        access_denied = 0
        
        if 'event_code' in df.columns:
            access_granted = len(df[df['event_code'].isin(EVENT_CODES['ACCESS_GRANTED'])])
            access_denied = len(df[df['event_code'].isin(EVENT_CODES['ACCESS_DENIED'])])
        
        return {
            'total_events': len(df),
            'access_granted': access_granted,
            'access_denied': access_denied,
            'unique_users': df['user_id'].nunique() if 'user_id' in df.columns else 0,
            'first_event': df['datetime'].min() if 'datetime' in df.columns else None,
            'last_event': df['datetime'].max() if 'datetime' in df.columns else None
        }
