"""
Módulo MovPer - Movimiento de Personal
Sistema de regularización de asistencias quincenal

Este módulo funciona como una aplicación independiente con su propio login.
"""

from flask import Blueprint, render_template, request, jsonify, send_file, session, redirect, url_for, after_this_request
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date, time as time_type
from calendar import monthrange
import os
import pytz
import json
import os
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment
from sqlalchemy import and_, or_, func
from sqlalchemy.orm.attributes import flag_modified
from webapp.models import db, MobPerUser, PresetUsuario, IncidenciaDia, Company
from src.api.biostar_client import BioStarAPIClient
from webapp.dias_inhabiles import obtener_dias_inhabiles, obtener_nombre_dia_inhabil
from src.utils.config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user
import time as time_module

mobper_bp = Blueprint('mobper', __name__, url_prefix='/mobper')

MEXICO_TZ = pytz.timezone('America/Mexico_City')

# =============================================================================
# CACHE DE BIOSTAR - Evita re-login y re-fetch en cada request
# =============================================================================

_biostar_client_cache = {
    'client': None,
    'last_login': 0,
    'ttl': 300  # 5 minutos de sesión válida
}

_biostar_events_cache = {}
_EVENTS_CACHE_TTL = 300  # 5 minutos

def get_biostar_client():
    """Obtiene un cliente BioStar reutilizando la sesión si es válida."""
    now = time_module.time()
    cache = _biostar_client_cache
    
    # Si el cliente existe y la sesión no ha expirado, reutilizar
    if cache['client'] and (now - cache['last_login']) < cache['ttl']:
        return cache['client']
    
    # Crear nuevo cliente y hacer login
    t0 = time_module.time()
    config = Config()
    biostar_cfg = config.biostar_config
    client = BioStarAPIClient(
        host=biostar_cfg['host'],
        username=biostar_cfg['username'],
        password=biostar_cfg['password']
    )
    
    if client.login():
        cache['client'] = client
        cache['last_login'] = now
        print(f"[MOVPER CACHE] BioStar login OK en {time_module.time()-t0:.2f}s (cached for {cache['ttl']}s)")
        return client
    else:
        print(f"[MOVPER CACHE] BioStar login FAILED en {time_module.time()-t0:.2f}s")
        cache['client'] = None
        return None

def get_cached_events(user_id, quincena_key, fetch_fn):
    """Cache de eventos por usuario+quincena. fetch_fn() se llama solo si no hay cache."""
    now = time_module.time()
    cache_key = f"{user_id}_{quincena_key}"
    
    if cache_key in _biostar_events_cache:
        entry = _biostar_events_cache[cache_key]
        if (now - entry['timestamp']) < _EVENTS_CACHE_TTL:
            print(f"[MOVPER CACHE] HIT eventos para {cache_key} (age: {now - entry['timestamp']:.0f}s)")
            return entry['data']
        else:
            print(f"[MOVPER CACHE] EXPIRED eventos para {cache_key}")
    
    # Cache miss - fetch
    t0 = time_module.time()
    data = fetch_fn()
    _biostar_events_cache[cache_key] = {'data': data, 'timestamp': now}
    print(f"[MOVPER CACHE] MISS eventos para {cache_key} - fetched en {time_module.time()-t0:.2f}s")
    return data

def invalidate_events_cache(user_id=None):
    """Invalida cache de eventos. Si user_id=None, invalida todo."""
    if user_id is None:
        _biostar_events_cache.clear()
    else:
        keys_to_remove = [k for k in _biostar_events_cache if k.startswith(f"{user_id}_")]
        for k in keys_to_remove:
            del _biostar_events_cache[k]

def prewarm_biostar_client():
    """Pre-calienta la conexión BioStar en background para que el primer request sea rápido."""
    import threading
    def _warm():
        try:
            print("[MOVPER CACHE] Pre-calentando conexion BioStar en background...")
            client = get_biostar_client()
            if client:
                print("[MOVPER CACHE] [OK] BioStar pre-calentado exitosamente")
            else:
                print("[MOVPER CACHE] [ERROR] BioStar pre-warm fallo")
        except Exception as e:
            print(f"[MOVPER CACHE] [ERROR] Error en pre-warm: {e}")
    
    t = threading.Thread(target=_warm, daemon=True)
    t.start()

# Nombres en español
DIAS_SEMANA = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
MESES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

def formatear_fecha_espanol(fecha):
    """Formatea fecha como 'Lunes 28 de Enero'"""
    dia_semana = DIAS_SEMANA[fecha.weekday()]
    mes = MESES[fecha.month]
    return f"{dia_semana} {fecha.day} de {mes}"

def normalizar_nombre_biostar(nombre_biostar: str) -> str:
    """
    Convierte nombre de BioStar (APELLIDO1 APELLIDO2 NOMBRE1 NOMBRE2)
    a formato normal (Nombre1 Nombre2 Apellido1 Apellido2) con Title Case.
    
    BioStar guarda: CETINA POOL RAUL ABEL
    Resultado: Raúl Abel Cetina Pool
    """
    if not nombre_biostar:
        return ''
    
    partes = nombre_biostar.strip().split()
    
    if len(partes) == 4:
        # APELLIDO1 APELLIDO2 NOMBRE1 NOMBRE2 → NOMBRE1 NOMBRE2 APELLIDO1 APELLIDO2
        nombre_reordenado = f"{partes[2]} {partes[3]} {partes[0]} {partes[1]}"
    elif len(partes) == 3:
        # APELLIDO1 NOMBRE1 NOMBRE2 o APELLIDO1 APELLIDO2 NOMBRE1
        # Asumimos: APELLIDO1 APELLIDO2 NOMBRE1 → NOMBRE1 APELLIDO1 APELLIDO2
        nombre_reordenado = f"{partes[2]} {partes[0]} {partes[1]}"
    elif len(partes) == 2:
        # APELLIDO NOMBRE → NOMBRE APELLIDO
        nombre_reordenado = f"{partes[1]} {partes[0]}"
    else:
        nombre_reordenado = nombre_biostar
    
    return aplicar_title_case(nombre_reordenado)

def aplicar_title_case(texto: str) -> str:
    """
    Aplica Title Case respetando acentos.
    'RAUL ABEL CETINA POOL' → 'Raul Abel Cetina Pool'
    'raul abel' → 'Raul Abel'
    'MARÍA JOSÉ' → 'María José'
    """
    if not texto:
        return ''
    return ' '.join(palabra.capitalize() for palabra in texto.lower().split())

def obtener_nombre_clasificacion(codigo):
    """Retorna el nombre en español de una clasificación"""
    nombres = {
        'REMOTO': 'Trabajo Remoto',
        'GUARDIA': 'Guardia',
        'PERMISO': 'Permiso',
        'VACACIONES': 'Vacaciones',
        'INHABIL': 'Día Inhábil',
        'INCAPACIDAD': 'Incapacidad'
    }
    return nombres.get(codigo, codigo)

def generar_motivo_auto(estado_auto, clasificacion, numero_dia):
    """Genera el motivo automático según el tipo de incidencia"""
    if estado_auto == 'RETARDO':
        return f"{numero_dia} retardo justificado"
    elif estado_auto == 'FALTA':
        motivos = {
            'REMOTO': f"{numero_dia} falta justificada, trabajo remoto",
            'GUARDIA': f"{numero_dia} falta justificada, guardia",
            'PERMISO': f"{numero_dia} falta justificada, permiso",
            'VACACIONES': f"{numero_dia} falta justificada, vacaciones",
            'INCAPACIDAD': f"{numero_dia} falta justificada, incapacidad",
            'INHABIL': f"{numero_dia} día inhábil"
        }
        return motivos.get(clasificacion, f"{numero_dia} falta")
    return ""

def now_cdmx():
    """Retorna datetime actual en zona horaria CDMX"""
    return datetime.now(MEXICO_TZ)

# ============================================================================
# AUTENTICACIÓN PERSONALIZADA PARA MOVPER
# ============================================================================

def mobper_login_required(f):
    """Decorador para proteger rutas de MovPer"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'mobper_user_id' not in session:
            return redirect(url_for('mobper.login'))
        return f(*args, **kwargs)
    return decorated_function

def mobper_admin_required(f):
    """Decorador para proteger rutas de admin MovPer"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'mobper_user_id' not in session:
            return redirect(url_for('mobper.login'))
        user = MobPerUser.query.get(session['mobper_user_id'])
        if not user or not user.is_admin:
            return jsonify({'error': 'Acceso denegado'}), 403
        return f(*args, **kwargs)
    return decorated_function

def get_current_mobper_user():
    """Obtiene el usuario actual de MovPer desde la sesión"""
    if 'mobper_user_id' not in session:
        return None
    return MobPerUser.query.get(session['mobper_user_id'])

# ============================================================================
# UTILIDADES DE QUINCENAS
# ============================================================================

def calcular_quincena_actual(fecha=None):
    """
    Calcula la quincena actual basándose en la fecha proporcionada.
    
    Reglas:
    - Primera quincena: día 1 al 15
    - Segunda quincena: día 16 al último día del mes
    
    Args:
        fecha: datetime o None (usa fecha actual)
    
    Returns:
        dict: {
            'numero': 1 o 2,
            'inicio': date,
            'fin': date,
            'mes': int,
            'anio': int,
            'nombre': str (ej: "Primera quincena de enero 2026")
        }
    """
    if fecha is None:
        fecha = now_cdmx().date()
    elif isinstance(fecha, datetime):
        fecha = fecha.date()
    
    dia = fecha.day
    mes = fecha.month
    anio = fecha.year
    
    # Determinar si es primera o segunda quincena
    if dia <= 15:
        # Primera quincena: 1 al 15
        numero = 1
        inicio = date(anio, mes, 1)
        fin = date(anio, mes, 15)
    else:
        # Segunda quincena: 16 al último día del mes
        numero = 2
        ultimo_dia = monthrange(anio, mes)[1]
        inicio = date(anio, mes, 16)
        fin = date(anio, mes, ultimo_dia)
    
    # Nombre del mes en español
    meses = [
        'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
        'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
    ]
    nombre_mes = meses[mes - 1]
    
    nombre_quincena = f"{'Primera' if numero == 1 else 'Segunda'} quincena de {nombre_mes} {anio}"
    
    return {
        'numero': numero,
        'inicio': inicio,
        'fin': fin,
        'mes': mes,
        'anio': anio,
        'nombre': nombre_quincena,
        'dias_totales': (fin - inicio).days + 1
    }

def obtener_quincena_anterior(quincena_actual):
    """
    Obtiene la quincena anterior a la proporcionada.
    
    Args:
        quincena_actual: dict retornado por calcular_quincena_actual()
    
    Returns:
        dict: quincena anterior
    """
    if quincena_actual['numero'] == 1:
        # Si es primera quincena, la anterior es la segunda del mes anterior
        mes_anterior = quincena_actual['mes'] - 1
        anio_anterior = quincena_actual['anio']
        if mes_anterior == 0:
            mes_anterior = 12
            anio_anterior -= 1
        fecha_anterior = date(anio_anterior, mes_anterior, 20)  # Día 20 está en segunda quincena
    else:
        # Si es segunda quincena, la anterior es la primera del mismo mes
        fecha_anterior = date(quincena_actual['anio'], quincena_actual['mes'], 10)
    
    return calcular_quincena_actual(fecha_anterior)

def obtener_quincena_siguiente(quincena_actual):
    """
    Obtiene la quincena siguiente a la proporcionada.
    """
    if quincena_actual['numero'] == 2:
        # Si es segunda quincena, la siguiente es la primera del mes siguiente
        mes_siguiente = quincena_actual['mes'] + 1
        anio_siguiente = quincena_actual['anio']
        if mes_siguiente == 13:
            mes_siguiente = 1
            anio_siguiente += 1
        fecha_siguiente = date(anio_siguiente, mes_siguiente, 5)
    else:
        # Si es primera quincena, la siguiente es la segunda del mismo mes
        fecha_siguiente = date(quincena_actual['anio'], quincena_actual['mes'], 20)
    
    return calcular_quincena_actual(fecha_siguiente)

# ============================================================================
# MOTOR DE CÁLCULO DE INCIDENCIAS
# ============================================================================

def obtener_primer_registro_dia(biostar_user_id, fecha):
    """
    Obtiene el primer registro ACCESS_GRANTED del día para un usuario desde BioStar API.
    
    Args:
        biostar_user_id: ID del usuario en BioStar (string)
        fecha: date
    
    Returns:
        datetime o None
    """
    try:
        print(f"[MOVPER] Buscando eventos para usuario {biostar_user_id} en fecha {fecha}")
        
        # Inicializar cliente BioStar
        config = Config()
        biostar_cfg = config.biostar_config
        client = BioStarAPIClient(
            host=biostar_cfg['host'],
            username=biostar_cfg['username'],
            password=biostar_cfg['password']
        )
        
        if not client.login():
            print(f"[MOVPER] Error: No se pudo autenticar con BioStar")
            return None
        
        # Calcular timestamps para el día completo
        inicio_dia = datetime.combine(fecha, datetime.min.time())
        fin_dia = datetime.combine(fecha, datetime.max.time())
        
        # Convertir a timezone aware
        inicio_dia = MEXICO_TZ.localize(inicio_dia)
        fin_dia = MEXICO_TZ.localize(fin_dia)
        
        print(f"[MOVPER] Rango: {inicio_dia} a {fin_dia}")
        
        # Buscar eventos del usuario en ese día usando search_events
        # Usar estructura correcta: user_id.user_id y datetime con operador BETWEEN
        conditions = [
            {
                "column": "user_id.user_id",
                "operator": 0,  # EQUAL
                "values": [biostar_user_id]
            },
            {
                "column": "datetime",
                "operator": 3,  # BETWEEN
                "values": [
                    inicio_dia.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    fin_dia.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                ]
            }
        ]
        
        eventos = client.search_events(conditions=conditions, limit=1000, descending=False)
        
        print(f"[MOVPER] Eventos encontrados: {len(eventos)}")
        
        if not eventos:
            print(f"[MOVPER] No se encontraron eventos")
            return None
        
        # Filtrar solo eventos ACCESS_GRANTED y obtener el primero
        # Códigos de ACCESS_GRANTED según BioStar 2 API
        ACCESS_GRANTED_CODES = [
            '4097', '4098', '4099', '4100', '4101', '4102', '4103', '4104', '4105', '4106', '4107',
            '4112', '4113', '4114', '4115', '4118', '4119', '4120', '4121', '4122', '4123', '4128', '4129',
            '4865', '4866', '4867', '4868', '4869', '4870', '4871', '4872'
        ]
        
        eventos_granted = [
            e for e in eventos 
            if e.get('event_type_id', {}).get('code') in ACCESS_GRANTED_CODES
        ]
        
        print(f"[MOVPER] Eventos ACCESS_GRANTED: {len(eventos_granted)}")
        
        if not eventos_granted:
            if eventos:
                print(f"[MOVPER] Primer evento código: {eventos[0].get('event_type_id', {}).get('code')}")
            return None
        
        # Ordenar por fecha y obtener el primero
        eventos_granted.sort(key=lambda x: x.get('datetime', ''))
        primer_evento = eventos_granted[0]
        
        print(f"[MOVPER] Primer registro: {primer_evento.get('datetime')}")
        
        # Parsear datetime
        from dateutil import parser
        dt = parser.parse(primer_evento['datetime'])
        
        # Asegurar que tiene timezone
        if dt.tzinfo is None:
            dt = MEXICO_TZ.localize(dt)
        else:
            dt = dt.astimezone(MEXICO_TZ)
        
        print(f"[MOVPER] Hora local: {dt.strftime('%H:%M:%S')}")
        
        return dt
        
    except Exception as e:
        print(f"[MOVPER] Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def calcular_incidencias_quincena(user, quincena):
    """
    Calcula las incidencias automáticas para una quincena completa.
    OPTIMIZADO: Obtiene todos los registros en UNA sola llamada API.
    
    Args:
        user: Usuario MovPer
        quincena: Dict con 'inicio', 'fin', 'nombre', 'anio', 'mes', 'numero'
        
    Returns:
        Lista de diccionarios con información de cada día
    """
    # Obtener o crear preset del usuario
    preset = PresetUsuario.query.filter_by(user_id=user.id).first()
    
    if not preset:
        # Crear preset por defecto si no existe
        preset = PresetUsuario(
            user_id=user.id,
            nombre_formato=user.nombre_completo,
            departamento_formato='',
            jefe_directo_nombre='',
            hora_entrada_default=datetime.strptime('09:00:00', '%H:%M:%S').time(),
            tolerancia_segundos=600,  # 10 minutos
            dias_descanso=[5, 6],  # Sábado y Domingo
            lista_inhabiles=[],
            vigente_desde=quincena['inicio']
        )
        db.session.add(preset)
        db.session.commit()
    
    hora_entrada_default = preset.hora_entrada_default
    tolerancia_segundos = preset.tolerancia_segundos
    dias_descanso = preset.dias_descanso or [5, 6]
    
    # Obtener días inhábiles oficiales del año de la quincena
    anio_quincena = quincena['inicio'].year
    dias_inhabiles_oficiales = obtener_dias_inhabiles(anio_quincena)
    
    # Combinar días inhábiles del preset con los oficiales
    lista_inhabiles_preset = preset.lista_inhabiles or []
    lista_inhabiles = list(set(lista_inhabiles_preset + dias_inhabiles_oficiales))
    
    # Usar numero_socio como biostar_user_id
    biostar_user_id = user.numero_socio
    
    # Calcular hora límite
    hora_limite_dt = datetime.combine(date.today(), hora_entrada_default) + timedelta(seconds=tolerancia_segundos)
    hora_limite = hora_limite_dt.time()
    
    incidencias = []
    fecha_actual = quincena['inicio']
    
    # Cargar clasificaciones guardadas para esta quincena
    clasificaciones_guardadas = {}
    incidencias_db = IncidenciaDia.query.filter(
        IncidenciaDia.user_id == user.id,
        IncidenciaDia.fecha >= quincena['inicio'],
        IncidenciaDia.fecha <= quincena['fin']
    ).all()
    
    for inc in incidencias_db:
        clasificaciones_guardadas[inc.fecha] = {
            'clasificacion': inc.clasificacion,
            'motivo_auto': inc.motivo_auto,
            'con_goce_sueldo': inc.con_goce_sueldo,
            'justificado': inc.justificado if hasattr(inc, 'justificado') else True
        }
    
    # OPTIMIZACIÓN: Obtener TODOS los registros con CACHE
    ACCESS_GRANTED_CODES = frozenset([
        '4097', '4098', '4099', '4100', '4101', '4102', '4103', '4104', '4105', '4106', '4107',
        '4112', '4113', '4114', '4115', '4118', '4119', '4120', '4121', '4122', '4123', '4128', '4129',
        '4865', '4866', '4867', '4868', '4869', '4870', '4871', '4872'
    ])
    
    quincena_key = f"{quincena['inicio']}_{quincena['fin']}"
    
    def fetch_events():
        """Función que obtiene eventos de BioStar (solo se llama en cache miss)."""
        registros = {}
        client = get_biostar_client()
        if not client:
            print(f"[MOVPER OPTIMIZADO] Error: No se pudo obtener cliente BioStar")
            return registros
        
        inicio_quincena = datetime.combine(quincena['inicio'], datetime.min.time())
        fin_quincena = datetime.combine(quincena['fin'], datetime.max.time())
        inicio_quincena = MEXICO_TZ.localize(inicio_quincena)
        fin_quincena = MEXICO_TZ.localize(fin_quincena)
        
        conditions = [
            {"column": "user_id.user_id", "operator": 0, "values": [biostar_user_id]},
            {"column": "datetime", "operator": 3, "values": [
                inicio_quincena.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                fin_quincena.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            ]}
        ]
        
        eventos = client.search_events(conditions=conditions, limit=1000, descending=False)
        print(f"[MOVPER OPTIMIZADO] Eventos encontrados: {len(eventos)}")
        
        for evento in eventos:
            event_code = evento.get('event_type_id', {}).get('code')
            if event_code in ACCESS_GRANTED_CODES:
                dt_str = evento.get('datetime')
                if dt_str:
                    dt_utc = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                    dt_utc = pytz.UTC.localize(dt_utc)
                    dt = dt_utc.astimezone(MEXICO_TZ)
                    fecha_evento = dt.date()
                    
                    if fecha_evento not in registros or dt < registros[fecha_evento]:
                        registros[fecha_evento] = dt
        
        print(f"[MOVPER OPTIMIZADO] Total días con registro: {len(registros)}")
        return registros
    
    try:
        registros_quincena = get_cached_events(user.id, quincena_key, fetch_events)
    except Exception as e:
        print(f"[MOVPER OPTIMIZADO] Error obteniendo registros de quincena: {e}")
        import traceback
        traceback.print_exc()
        registros_quincena = {}
    
    while fecha_actual <= quincena['fin']:
        dia_semana = fecha_actual.weekday()
        
        # Paso 1: Clasificar tipo de día
        if fecha_actual in lista_inhabiles:
            tipo_dia = 'INHABIL'
            estado_auto = 'INHABIL'
            primer_registro = None
            minutos_diferencia = None
            nombre_inhabil = obtener_nombre_dia_inhabil(fecha_actual)
        elif dia_semana in dias_descanso:
            tipo_dia = 'DESCANSO'
            estado_auto = 'DESCANSO'
            primer_registro = None
            minutos_diferencia = None
        else:
            tipo_dia = 'LABORAL'
            
            # Paso 2: Usar registro precargado (ya no hacemos llamada API aquí)
            primer_registro = registros_quincena.get(fecha_actual)
            
            if primer_registro is None:
                # Sin registro = FALTA
                estado_auto = 'FALTA'
                minutos_diferencia = None
            else:
                # Comparar con hora límite
                hora_registro = primer_registro.time()
                
                # Calcular diferencia en segundos totales
                entrada_dt = datetime.combine(date.today(), hora_entrada_default)
                registro_dt = datetime.combine(date.today(), hora_registro)
                diferencia_segundos = (registro_dt - entrada_dt).total_seconds()
                minutos_diferencia = int(diferencia_segundos / 60)
                
                # Comparar con hora límite: si llega ANTES de que termine el minuto límite, es a tiempo
                # Ejemplo: límite 09:10, si llega a las 09:10:59 es a tiempo, 09:11:00 es retardo
                limite_dt = datetime.combine(date.today(), hora_limite)
                # Agregar 59 segundos al límite para que todo el minuto cuente como a tiempo
                limite_con_segundos = limite_dt + timedelta(seconds=59)
                
                if registro_dt <= limite_con_segundos:
                    estado_auto = 'A_TIEMPO'
                else:
                    estado_auto = 'RETARDO'
        
        # Obtener clasificación guardada si existe
        clasificacion_info = clasificaciones_guardadas.get(fecha_actual, {})
        
        incidencia_dict = {
            'fecha': fecha_actual,
            'dia_semana': dia_semana,
            'tipo_dia': tipo_dia,
            'primer_registro': primer_registro,
            'estado_auto': estado_auto,
            'minutos_diferencia': minutos_diferencia,
            'hora_entrada_esperada': hora_entrada_default,
            'hora_limite': hora_limite,
            'clasificacion': clasificacion_info.get('clasificacion'),
            'motivo_auto': clasificacion_info.get('motivo_auto'),
            'con_goce_sueldo': clasificacion_info.get('con_goce_sueldo', True),
            'justificado': clasificacion_info.get('justificado', True)
        }
        
        # Agregar nombre del día inhábil si aplica
        if estado_auto == 'INHABIL':
            incidencia_dict['nombre_inhabil'] = nombre_inhabil
        
        incidencias.append(incidencia_dict)
        
        fecha_actual += timedelta(days=1)
    
    return incidencias

# ============================================================================
# RUTAS
# ============================================================================

@mobper_bp.route('/')
def mobper_root():
    """
    Ruta raíz de MovPer - redirige a login o dashboard según estado de autenticación.
    """
    if 'mobper_user_id' in session:
        # Usuario autenticado, redirigir a dashboard
        return redirect(url_for('mobper.dashboard'))
    else:
        # No autenticado, redirigir a login
        return redirect(url_for('mobper.login'))

@mobper_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Página de login para usuarios existentes.
    """
    if request.method == 'POST':
        numero_socio = request.form.get('numero_socio', '').strip()
        password = request.form.get('password', '').strip()
        
        if not numero_socio or not password:
            return render_template('mobper_login_new.html', 
                                 error='Ingresa tu número de empleado y contraseña',
                                 numero_socio=numero_socio)
        
        # Buscar usuario
        user = MobPerUser.query.filter_by(numero_socio=numero_socio).first()
        
        if not user:
            return render_template('mobper_login_new.html', 
                                 error='Usuario no encontrado. ¿Necesitas registrarte?',
                                 numero_socio=numero_socio)
        
        if not user.check_password(password):
            return render_template('mobper_login_new.html', 
                                 error='Contraseña incorrecta',
                                 numero_socio=numero_socio)
        
        # Login exitoso
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        session['mobper_user_id'] = user.id
        session['mobper_numero_socio'] = user.numero_socio
        
        return redirect(url_for('mobper.checklist'))
    
    return render_template('mobper_login_new.html')

@mobper_bp.route('/register', methods=['GET'])
def register_page():
    """Página de registro"""
    return render_template('mobper_register.html')

@mobper_bp.route('/register', methods=['POST'])
def register():
    """Procesar registro de nuevo usuario"""
    numero_socio = request.form.get('numero_socio', '').strip()
    nombre = request.form.get('nombre', '').strip()
    password = request.form.get('password', '').strip()
    password_confirm = request.form.get('password_confirm', '').strip()
    
    if not numero_socio or not nombre or not password:
        return render_template('mobper_register.html', 
                             error='Completa todos los campos',
                             numero_socio=numero_socio,
                             nombre=nombre)
    
    if password != password_confirm:
        return render_template('mobper_register.html', 
                             error='Las contraseñas no coinciden',
                             numero_socio=numero_socio,
                             nombre=nombre)
    
    # Verificar si ya existe
    if MobPerUser.query.filter_by(numero_socio=numero_socio).first():
        return render_template('mobper_register.html', 
                             error='Este número de empleado ya está registrado. Inicia sesión.',
                             numero_socio=numero_socio)
    
    # Validar con BioStar
    try:
        config = Config()
        biostar_cfg = config.biostar_config
        client = BioStarAPIClient(
            host=biostar_cfg['host'],
            username=biostar_cfg['username'],
            password=biostar_cfg['password']
        )
        
        if not client.login():
            return render_template('mobper_register.html', 
                                 error='Error conectando con BioStar. Intenta más tarde.',
                                 numero_socio=numero_socio,
                                 nombre=nombre)
        
        # Buscar usuario en BioStar
        print(f"[MOVPER] Buscando usuario {numero_socio} en BioStar...")
        usuarios = client.get_all_users(limit=3000)
        print(f"[MOVPER] Total usuarios obtenidos: {len(usuarios)}")
        
        usuario_biostar = None
        
        for u in usuarios:
            if u.get('user_id') == numero_socio:
                usuario_biostar = u
                print(f"[MOVPER] Usuario encontrado: {u.get('name')}")
                break
        
        if not usuario_biostar:
            print(f"[MOVPER] Usuario {numero_socio} NO encontrado")
            return render_template('mobper_register.html', 
                                 error=f'Número de empleado {numero_socio} no encontrado en BioStar. Verifica que sea correcto.',
                                 numero_socio=numero_socio,
                                 nombre=nombre)
        
        # Validar nombre (primer nombre + apellido)
        nombre_biostar = usuario_biostar.get('name', '').lower()
        nombre_ingresado = nombre.lower()
        
        # Verificar que al menos coincida parcialmente
        palabras_biostar = nombre_biostar.split()
        palabras_ingresadas = nombre_ingresado.split()
        
        coincide = False
        if len(palabras_ingresadas) >= 2:
            # Verificar primer nombre + apellido
            primer_nombre = palabras_ingresadas[0]
            apellido = palabras_ingresadas[1]
            
            if primer_nombre in palabras_biostar and apellido in palabras_biostar:
                coincide = True
        
        if not coincide:
            return render_template('mobper_register.html', 
                                 error=f'El nombre no coincide. En BioStar apareces como: {usuario_biostar.get("name")}',
                                 numero_socio=numero_socio,
                                 nombre=nombre)
        
        # Reordenar nombre de BioStar y aplicar Title Case
        nombre_normalizado = normalizar_nombre_biostar(usuario_biostar.get('name', ''))
        print(f"[MOVPER] Nombre BioStar original: {usuario_biostar.get('name')}")
        print(f"[MOVPER] Nombre normalizado: {nombre_normalizado}")
        
        # Crear nuevo usuario (8490 es admin por defecto)
        ADMIN_NUMEROS = {'8490'}
        nuevo_user = MobPerUser(
            numero_socio=numero_socio,
            nombre_completo=nombre_normalizado,
            is_admin=(numero_socio in ADMIN_NUMEROS)
        )
        nuevo_user.set_password(password)
        
        db.session.add(nuevo_user)
        db.session.commit()
        
        # Crear preset inicial con nombre normalizado
        preset_inicial = PresetUsuario(
            user_id=nuevo_user.id,
            nombre_formato=nombre_normalizado,
            departamento_formato='',
            jefe_directo_nombre='',
            hora_entrada_default=datetime.strptime('09:00:00', '%H:%M:%S').time(),
            tolerancia_segundos=600,
            dias_descanso=[5, 6],
            lista_inhabiles=[],
            vigente_desde=date.today()
        )
        db.session.add(preset_inicial)
        db.session.commit()
        
        # Crear sesión automáticamente
        session['mobper_user_id'] = nuevo_user.id
        session['mobper_numero_socio'] = nuevo_user.numero_socio
        
        # Marcar que es primera configuración
        session['mobper_first_config'] = True
        
        # Redirigir a config para completar info inicial (única vez)
        return redirect(url_for('mobper.config'))
        
    except Exception as e:
        print(f"[MOVPER] Error en registro: {e}")
        import traceback
        traceback.print_exc()
        return render_template('mobper_register.html', 
                             error=f'Error validando con BioStar: {str(e)}',
                             numero_socio=numero_socio,
                             nombre=nombre)

@mobper_bp.route('/logout')
def logout():
    """Cerrar sesión de MobPer"""
    session.pop('mobper_user_id', None)
    session.pop('mobper_numero_socio', None)
    return redirect(url_for('mobper.login'))

@mobper_bp.route('/config', methods=['GET', 'POST'])
@mobper_login_required
def config():
    """Configuración de horarios y preset del usuario"""
    user = get_current_mobper_user()
    preset = PresetUsuario.query.filter_by(user_id=user.id).first()
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre_formato = aplicar_title_case(request.form.get('nombre_formato', '').strip())
            departamento_formato = request.form.get('departamento_formato', '').strip().upper()
            jefe_directo_nombre = aplicar_title_case(request.form.get('jefe_directo_nombre', '').strip())
            
            # Empresa
            company_id = request.form.get('company_id')
            company_id = int(company_id) if company_id and company_id.strip() else None
            
            hora_entrada_str = request.form.get('hora_entrada_default', '09:00')
            hora_entrada = datetime.strptime(hora_entrada_str, '%H:%M').time()
            
            tolerancia_minutos = int(request.form.get('tolerancia_minutos', 10))
            tolerancia_segundos = tolerancia_minutos * 60
            
            # Días de descanso
            dias_descanso = [int(d) for d in request.form.getlist('dias_descanso')]
            
            # Crear o actualizar preset (días inhábiles se manejan globalmente)
            if not preset:
                preset = PresetUsuario(
                    user_id=user.id,
                    nombre_formato=nombre_formato,
                    departamento_formato=departamento_formato,
                    jefe_directo_nombre=jefe_directo_nombre,
                    company_id=company_id,
                    hora_entrada_default=hora_entrada,
                    tolerancia_segundos=tolerancia_segundos,
                    dias_descanso=dias_descanso,
                    lista_inhabiles=[],
                    vigente_desde=date.today()
                )
                db.session.add(preset)
            else:
                preset.nombre_formato = nombre_formato
                preset.departamento_formato = departamento_formato
                preset.jefe_directo_nombre = jefe_directo_nombre
                preset.company_id = company_id
                preset.hora_entrada_default = hora_entrada
                preset.tolerancia_segundos = tolerancia_segundos
                preset.dias_descanso = dias_descanso
                flag_modified(preset, 'dias_descanso')
            
            print(f"[MOVPER CONFIG] Guardando dias_descanso={dias_descanso} para user_id={user.id}")
            db.session.commit()
            
            # Verificar que se guardó correctamente
            db.session.refresh(preset)
            print(f"[MOVPER CONFIG] Verificacion post-save: dias_descanso={preset.dias_descanso}")
            
            # Si es primera configuración (post-registro), ir al checklist
            if session.pop('mobper_first_config', False):
                return redirect(url_for('mobper.checklist'))
            
            # Si no, quedarse en config con mensaje de éxito
            return redirect(url_for('mobper.config', saved=1))
        
        except Exception as e:
            db.session.rollback()
            companies = Company.query.filter_by(is_active=True).order_by(Company.name).all()
            return render_template('mobper_config.html', 
                                 user=user, 
                                 preset=preset,
                                 companies=companies,
                                 error=f'Error al guardar configuración: {str(e)}')
    
    # Si viene de guardar exitosamente
    success_msg = 'Configuración guardada exitosamente' if request.args.get('saved') else None
    companies = Company.query.filter_by(is_active=True).order_by(Company.name).all()
    return render_template('mobper_config.html', user=user, preset=preset, companies=companies, success=success_msg)

@mobper_bp.route('/api/clasificar-dia', methods=['POST'])
@mobper_login_required
def api_clasificar_dia():
    """Guardar clasificación de un día específico"""
    try:
        user = get_current_mobper_user()
        data = request.get_json()
        
        print(f"[MOVPER API] Datos recibidos: {data}")
        
        fecha_str = data.get('fecha')
        clasificacion = data.get('clasificacion')
        estado_auto = data.get('estado_auto')
        numero_dia = data.get('numero_dia', 1)
        
        print(f"[MOVPER API] Procesando: fecha={fecha_str}, clasificacion={clasificacion}, estado_auto={estado_auto}, numero_dia={numero_dia}")
        
        if not fecha_str or not clasificacion:
            print(f"[MOVPER API] Error: Datos incompletos")
            return jsonify({'success': False, 'error': 'Datos incompletos'}), 400
        
        # Parsear fecha
        from datetime import datetime as dt
        fecha = dt.strptime(fecha_str, '%Y-%m-%d').date()
        
        # Buscar o crear incidencia
        incidencia = IncidenciaDia.query.filter_by(
            user_id=user.id,
            fecha=fecha
        ).first()
        
        if not incidencia:
            print(f"[MOVPER API] Creando nueva incidencia para {fecha}")
            incidencia = IncidenciaDia(
                user_id=user.id,
                fecha=fecha,
                estado_auto=estado_auto
            )
            db.session.add(incidencia)
        else:
            print(f"[MOVPER API] Actualizando incidencia existente para {fecha}")
        
        incidencia.clasificacion = clasificacion
        incidencia.motivo_auto = generar_motivo_auto(estado_auto, clasificacion, numero_dia)
        incidencia.updated_at = datetime.utcnow()
        
        print(f"[MOVPER API] Guardando: clasificacion={incidencia.clasificacion}, motivo={incidencia.motivo_auto}")
        
        db.session.commit()
        
        print(f"[MOVPER API] Guardado exitoso")
        
        return jsonify({
            'success': True,
            'motivo': incidencia.motivo_auto
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"[MOVPER API] Error en api_clasificar_dia: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@mobper_bp.route('/api/clasificar-multiple', methods=['POST'])
@mobper_login_required
def api_clasificar_multiple():
    """Aplicar clasificación a múltiples días (atajos rápidos)"""
    try:
        user = get_current_mobper_user()
        data = request.get_json()
        
        items = data.get('items', [])  # Lista de {fecha, estado_auto, numero_dia}
        clasificacion = data.get('clasificacion')
        
        if not items or not clasificacion:
            return jsonify({'success': False, 'error': 'Datos incompletos'}), 400
        
        from datetime import datetime as dt
        count = 0
        
        for item in items:
            fecha = dt.strptime(item['fecha'], '%Y-%m-%d').date()
            estado_auto = item.get('estado_auto', 'FALTA')
            numero_dia = item.get('numero_dia', count + 1)
            
            incidencia = IncidenciaDia.query.filter_by(
                user_id=user.id,
                fecha=fecha
            ).first()
            
            if not incidencia:
                incidencia = IncidenciaDia(
                    user_id=user.id,
                    fecha=fecha,
                    estado_auto=estado_auto
                )
                db.session.add(incidencia)
            
            incidencia.clasificacion = clasificacion
            incidencia.motivo_auto = generar_motivo_auto(estado_auto, clasificacion, numero_dia)
            incidencia.updated_at = datetime.utcnow()
            count += 1
        
        db.session.commit()
        
        return jsonify({'success': True, 'count': count})
    
    except Exception as e:
        db.session.rollback()
        print(f"[MOVPER] Error en api_clasificar_multiple: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mobper_bp.route('/api/check-user', methods=['POST'])
def api_check_user():
    """Verifica si un número de socio ya está registrado"""
    data = request.get_json()
    numero_socio = data.get('numero_socio', '').strip()
    
    if not numero_socio:
        return jsonify({'exists': False})
    
    user = MobPerUser.query.filter_by(numero_socio=numero_socio).first()
    return jsonify({'exists': user is not None})

@mobper_bp.route('/checklist', methods=['GET'])
@mobper_bp.route('/checklist/<int:year>/<int:month>/<int:quincena_num>', methods=['GET'])
@mobper_login_required
def checklist(year=None, month=None, quincena_num=None):
    """
    Pantalla principal del checklist de incidencias.
    Mobile-first con código de colores.
    Soporta navegación entre quincenas.
    """
    t_start = time_module.time()
    user = get_current_mobper_user()
    
    # Calcular quincena (actual o especificada)
    if year and month and quincena_num:
        quincena = calcular_quincena(year, month, quincena_num)
    else:
        # Por defecto, mostrar la quincena ANTERIOR (la que se debe justificar)
        # ya que la actual aún está en curso
        quincena_actual = calcular_quincena_actual()
        quincena = obtener_quincena_anterior(quincena_actual)
    
    # Calcular quincenas para navegación
    quincena_anterior = obtener_quincena_anterior(quincena)
    quincena_siguiente = obtener_quincena_siguiente(quincena)
    
    # Calcular incidencias automáticas
    t_api = time_module.time()
    incidencias = calcular_incidencias_quincena(user, quincena)
    print(f"[MOVPER PERF] calcular_incidencias_quincena: {time_module.time()-t_api:.2f}s")
    
    # Calcular resumen
    resumen = {
        'a_tiempo': sum(1 for i in incidencias if i['estado_auto'] == 'A_TIEMPO'),
        'retardos': sum(1 for i in incidencias if i['estado_auto'] == 'RETARDO'),
        'faltas': sum(1 for i in incidencias if i['estado_auto'] == 'FALTA'),
        'inhabiles': sum(1 for i in incidencias if i['estado_auto'] == 'INHABIL'),
        'descansos': sum(1 for i in incidencias if i['estado_auto'] == 'DESCANSO'),
        'total': len(incidencias)
    }
    
    # Determinar si la quincena siguiente ya inició (para habilitar navegación)
    from datetime import date as date_type
    hoy = date_type.today()
    puede_ir_siguiente = quincena_siguiente['inicio'] <= hoy
    
    print(f"[MOVPER PERF] Total checklist route: {time_module.time()-t_start:.2f}s")
    
    return render_template(
        'mobper_checklist_v3.html',
        quincena=quincena,
        incidencias=incidencias,
        resumen=resumen,
        user=user,
        formatear_fecha=formatear_fecha_espanol,
        obtener_nombre_clasificacion=obtener_nombre_clasificacion,
        quincena_anterior=quincena_anterior,
        quincena_siguiente=quincena_siguiente,
        puede_ir_siguiente=puede_ir_siguiente
    )

@mobper_bp.route('/api/calcular-quincena', methods=['POST'])
@mobper_login_required
def api_calcular_quincena():
    """
    API para calcular incidencias de una quincena específica.
    """
    user = get_current_mobper_user()
    data = request.get_json()
    
    # Obtener fecha de referencia
    if 'fecha' in data:
        fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
    else:
        fecha = now_cdmx().date()
    
    # Calcular quincena
    quincena = calcular_quincena_actual(fecha)
    
    # Calcular incidencias
    incidencias = calcular_incidencias_quincena(user, quincena)
    
    # Serializar para JSON
    incidencias_json = []
    for inc in incidencias:
        incidencias_json.append({
            'fecha': inc['fecha'].isoformat(),
            'dia_semana': inc['dia_semana'],
            'tipo_dia': inc['tipo_dia'],
            'primer_registro': inc['primer_registro'].isoformat() if inc['primer_registro'] else None,
            'estado_auto': inc['estado_auto'],
            'minutos_diferencia': inc['minutos_diferencia'],
            'hora_entrada_esperada': inc['hora_entrada_esperada'].strftime('%H:%M:%S'),
            'hora_limite': inc['hora_limite'].strftime('%H:%M:%S')
        })
    
    return jsonify({
        'success': True,
        'quincena': {
            'numero': quincena['numero'],
            'inicio': quincena['inicio'].isoformat(),
            'fin': quincena['fin'].isoformat(),
            'nombre': quincena['nombre'],
            'dias_totales': quincena['dias_totales']
        },
        'incidencias': incidencias_json
    })

@mobper_bp.route('/api/exportar-excel', methods=['POST'])
@mobper_login_required
def api_exportar_excel():
    """
    Exporta el formato Excel prellenado con las incidencias.
    Usa win32com para preservar formatos y shapes.
    """
    from webapp.mobper_excel import generar_formato_excel
    
    user = get_current_mobper_user()
    data = request.get_json()
    
    # Calcular quincena
    if 'fecha' in data:
        fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
    else:
        fecha = now_cdmx().date()
    
    quincena = calcular_quincena_actual(fecha)
    incidencias = calcular_incidencias_quincena(user, quincena)
    
    # Obtener preset del usuario
    preset = PresetUsuario.query.filter_by(user_id=user.id).first()
    
    # Determinar si es con goce de sueldo (por defecto sí)
    con_goce = data.get('con_goce', True)
    
    try:
        # Generar Excel con win32com
        output_path, output_filename = generar_formato_excel(
            user=user,
            preset=preset,
            incidencias=incidencias,
            quincena=quincena,
            con_goce=con_goce
        )
        
        # Enviar archivo al cliente y borrar después
        @after_this_request
        def remove_file(response):
            try:
                os.remove(output_path)
                print(f"[MOVPER ROUTES] Archivo temporal eliminado: {output_path}")
            except Exception as e:
                print(f"[MOVPER ROUTES] Error al eliminar archivo temporal: {e}")
            return response
        
        return send_file(
            output_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=output_filename
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'message': f'Error al generar Excel: {str(e)}'
        }), 500


@mobper_bp.route('/api/previsualizar', methods=['POST'])
@mobper_login_required
def api_previsualizar():
    """
    Genera una vista previa del formato en HTML.
    """
    user = get_current_mobper_user()
    data = request.get_json()
    
    # Calcular quincena
    if 'fecha' in data:
        fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
    else:
        fecha = now_cdmx().date()
    
    quincena = calcular_quincena_actual(fecha)
    incidencias = calcular_incidencias_quincena(user, quincena)
    
    # Filtrar incidencias
    dias_con_incidencias = [
        inc for inc in incidencias
        if inc['estado_auto'] in ['RETARDO', 'FALTA']
    ]
    
    return render_template(
        'mobper_preview.html',
        user=user,
        quincena=quincena,
        incidencias=dias_con_incidencias
    )

# ============================================================================
# UTILIDADES
# ============================================================================

def generar_fecha_aplicacion(dias, quincena):
    """
    Genera el texto de fecha de aplicación según las reglas.
    
    Ejemplos:
    - [1] → "1 de enero"
    - [13, 14] → "13 y 14 de enero"
    - [1,2,5,6,7,8,9,12,13,14,15] → "1,2,5,6,7,8,9,12,13,14,15 de enero"
    """
    meses = [
        'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
        'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
    ]
    nombre_mes = meses[quincena['mes'] - 1]
    
    if len(dias) == 0:
        return ""
    
    if len(dias) == 1:
        return f"{dias[0]} de {nombre_mes}"
    
    if len(dias) == 2:
        return f"{dias[0]} y {dias[1]} de {nombre_mes}"
    
    # 3 o más días: formato compacto sin espacios
    dias_str = ",".join(str(d) for d in dias)
    return f"{dias_str} de {nombre_mes}"


# =============================================================================
# NUEVAS RUTAS: Generación de Excel, Preview, Toggle Justificación
# =============================================================================

@mobper_bp.route('/api/toggle-justificacion', methods=['POST'])
@mobper_login_required
def toggle_justificacion():
    """Alternar justificación de un retardo."""
    try:
        data = request.get_json()
        fecha_str = data.get('fecha')
        justificado = data.get('justificado', True)
        
        user = get_current_mobper_user()
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        # Buscar o crear registro de incidencia
        incidencia = IncidenciaDia.query.filter_by(
            user_id=user.id,
            fecha=fecha
        ).first()
        
        if not incidencia:
            incidencia = IncidenciaDia(
                user_id=user.id,
                fecha=fecha,
                estado_auto='RETARDO'
            )
            db.session.add(incidencia)
        
        incidencia.justificado = justificado
        if justificado:
            incidencia.motivo_auto = 'Retardo justificado'
        else:
            incidencia.motivo_auto = 'Retardo NO justificado'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'justificado': justificado,
            'fecha': fecha_str
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@mobper_bp.route('/generar-excel')
@mobper_login_required
def generar_excel():
    """Genera el formato Excel de movimiento de personal."""
    try:
        from webapp.mobper_excel import generar_formato_excel
        
        user = get_current_mobper_user()
        preset = PresetUsuario.query.filter_by(user_id=user.id).first()
        
        # Obtener quincena especificada o la anterior (la que se está justificando)
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        quincena_num = request.args.get('quincena', type=int)
        
        if year and month and quincena_num:
            quincena = calcular_quincena(year, month, quincena_num)
        else:
            # Por defecto usar la quincena ANTERIOR (la que se justifica en el checklist)
            quincena_actual = calcular_quincena_actual()
            quincena = obtener_quincena_anterior(quincena_actual)
        
        # Calcular incidencias dinámicamente (igual que el checklist)
        incidencias_dict = calcular_incidencias_quincena(user, quincena)
        
        # Leer con_goce del parámetro del UI (1 = con goce, 0 = sin goce)
        con_goce_param = request.args.get('con_goce', '1')
        con_goce = con_goce_param == '1'
        
        print(f"[MOVPER ROUTES] === GENERAR EXCEL ===")
        print(f"[MOVPER ROUTES] Params recibidos: year={year}, month={month}, quincena_num={quincena_num}, con_goce={con_goce_param}")
        print(f"[MOVPER ROUTES] User: {user.nombre_completo}")
        print(f"[MOVPER ROUTES] Preset: {preset}")
        print(f"[MOVPER ROUTES] Quincena calculada: {quincena}")
        print(f"[MOVPER ROUTES] Incidencias totales: {len(incidencias_dict)}")
        print(f"[MOVPER ROUTES] Con goce: {con_goce}")
        
        # Log detallado de incidencias para debug
        for inc in incidencias_dict:
            if inc.get('estado_auto') in ('RETARDO', 'FALTA'):
                print(f"[MOVPER ROUTES]   {inc['fecha']} - {inc['estado_auto']} | clasificacion={inc.get('clasificacion')} | justificado={inc.get('justificado')} | motivo={inc.get('motivo_auto')}")
        
        # Generar Excel
        output_path, filename = generar_formato_excel(
            user=user,
            preset=preset,
            incidencias=incidencias_dict,
            quincena=quincena,
            con_goce=con_goce
        )
        
        # Descargar archivo directamente y borrar después
        @after_this_request
        def remove_file(response):
            try:
                os.remove(output_path)
                print(f"[MOVPER ROUTES] Archivo temporal eliminado: {output_path}")
            except Exception as e:
                print(f"[MOVPER ROUTES] Error al eliminar archivo temporal: {e}")
            return response

        return send_file(
            output_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# NOTA: Rutas obsoletas comentadas - ahora usamos archivos temporales
# @mobper_bp.route('/download/<filename>')
# @mobper_login_required
# def download_excel(filename):
#     """Descarga el archivo Excel generado."""
#     # Ya no se usa - los archivos se generan como temporales y se borran después de enviarse
#     return jsonify({'error': 'Ruta obsoleta - usa /generar_excel'}), 404


# @mobper_bp.route('/preview/<filename>')
# @mobper_login_required
# def preview_excel(filename):
#     """Vista previa del formato Excel como HTML."""
#     # Ya no se usa - los archivos se generan como temporales
#     return "Ruta obsoleta", 404


@mobper_bp.route('/formatos')
@mobper_login_required
def listar_formatos():
    """Lista los formatos Excel generados para el usuario."""
    from webapp.mobper_excel import obtener_formatos_generados
    
    user = get_current_mobper_user()
    formatos = obtener_formatos_generados(user.id)
    
    return render_template('mobper_formatos.html', 
                         user=user, 
                         formatos=formatos)


# Helper para navegación de quincenas
def obtener_quincena_anterior(quincena):
    """Obtiene la quincena anterior a la dada."""
    if quincena['numero'] == 1:
        # Primera quincena -> ir a segunda quincena del mes anterior
        mes_anterior = quincena['mes'] - 1
        anio = quincena['anio']
        if mes_anterior < 1:
            mes_anterior = 12
            anio -= 1
        return calcular_quincena(anio, mes_anterior, 2)
    else:
        # Segunda quincena -> ir a primera del mismo mes
        return calcular_quincena(quincena['anio'], quincena['mes'], 1)


def obtener_quincena_siguiente(quincena):
    """Obtiene la quincena siguiente a la dada."""
    if quincena['numero'] == 1:
        # Primera quincena -> ir a segunda del mismo mes
        return calcular_quincena(quincena['anio'], quincena['mes'], 2)
    else:
        # Segunda quincena -> ir a primera del mes siguiente
        mes_siguiente = quincena['mes'] + 1
        anio = quincena['anio']
        if mes_siguiente > 12:
            mes_siguiente = 1
            anio += 1
        return calcular_quincena(anio, mes_siguiente, 1)


def calcular_quincena(anio, mes, numero):
    """Calcula los límites de una quincena específica."""
    if numero == 1:
        inicio = date(anio, mes, 1)
        fin = date(anio, mes, 15)
    else:
        inicio = date(anio, mes, 16)
        ultimo_dia = monthrange(anio, mes)[1]
        fin = date(anio, mes, ultimo_dia)
    
    nombre = f"{'1ra' if numero == 1 else '2da'} Quincena de {MESES[mes]} {anio}"
    
    return {
        'inicio': inicio,
        'fin': fin,
        'nombre': nombre,
        'numero': numero,
        'mes': mes,
        'anio': anio
    }


# ============================================================
# RUTAS DE PRUEBA WIN32COM EXCEL
# ============================================================

@mobper_bp.route('/test-excel', methods=['GET'])
def test_excel_page():
    """Página de prueba para métodos de edición Excel (DEPRECATED)."""
    # Redirigir a la nueva página
    return redirect(url_for('mobper.test_win32_page'))


@mobper_bp.route('/test-win32', methods=['GET'])
def test_win32_page():
    """Nueva página de prueba solo con Win32COM."""
    return render_template('excel_win32_test.html')


@mobper_bp.route('/test-win32/<test_id>', methods=['POST'])
def run_win32_test(test_id):
    """Ejecutar un escenario de prueba Win32COM."""
    from webapp.excel_win32_tests import (
        test_solo_retardo,
        test_solo_falta,
        test_falta_y_retardo,
        test_sin_goce_sueldo,
        test_olvido_checar,
        test_retirarse_temprano,
        test_formato_quincena_completa,
        test_salir_y_regresar,
    )
    
    tests_map = {
        'solo_retardo': test_solo_retardo,
        'solo_falta': test_solo_falta,
        'falta_y_retardo': test_falta_y_retardo,
        'sin_goce_sueldo': test_sin_goce_sueldo,
        'olvido_checar': test_olvido_checar,
        'retirarse_temprano': test_retirarse_temprano,
        'quincena_completa': test_formato_quincena_completa,
        'salir_regresar': test_salir_y_regresar,
    }
    
    if test_id not in tests_map:
        return jsonify({'success': False, 'error': f'Test no encontrado: {test_id}'})
    
    try:
        result = tests_map[test_id]()
        
        if result['success']:
            filename = os.path.basename(result['output_file'])
            return jsonify({
                'success': True,
                'filename': filename,
                'test_name': result['test_name'],
                'output_file': result['output_file']
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Error desconocido'),
                'test_name': result['test_name']
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'test_name': test_id
        })


@mobper_bp.route('/download-win32/<test_id>', methods=['GET'])
def download_win32_file(test_id):
    """Descargar archivo generado por un test Win32COM."""
    import glob
    
    output_dir = r"C:\Users\raulc\Downloads\debug biostar para checadores\webapp\output\excel_tests"
    
    # Buscar el archivo más reciente para este test
    pattern = os.path.join(output_dir, f"{test_id}_*.xlsx")
    files = glob.glob(pattern)
    
    if not files:
        return jsonify({'success': False, 'error': 'Archivo no encontrado'}), 404
    
    latest_file = max(files, key=os.path.getmtime)
    filename = os.path.basename(latest_file)
    
    return send_file(
        latest_file,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@mobper_bp.route('/output-folder', methods=['GET'])
def open_output_folder():
    """Abrir la carpeta de salida en el explorador."""
    import subprocess
    output_dir = r"C:\Users\raulc\Downloads\debug biostar para checadores\webapp\output\excel_tests"
    try:
        subprocess.Popen(f'explorer "{output_dir}"')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# =============================================================================
# ADMIN CRUD - PANEL DE ADMINISTRACIÓN DE USUARIOS MOVPER
# =============================================================================

@mobper_bp.route('/admin')
@mobper_admin_required
def admin_panel():
    """Panel de administración de usuarios MobPer."""
    current_user = get_current_mobper_user()
    users = MobPerUser.query.order_by(MobPerUser.created_at.desc()).all()
    return render_template('mobper_admin.html', users=users, current_user=current_user)


@mobper_bp.route('/admin/api/users', methods=['GET'])
@mobper_admin_required
def admin_api_users():
    """API: Lista todos los usuarios con sus presets."""
    users = MobPerUser.query.order_by(MobPerUser.created_at.desc()).all()
    result = []
    for u in users:
        empresa = ''
        if u.preset and u.preset.company_id and u.preset.company:
            empresa = u.preset.company.name
        result.append({
            'id': u.id,
            'numero_socio': u.numero_socio,
            'nombre_completo': u.nombre_completo,
            'is_active': u.is_active,
            'is_admin': u.is_admin,
            'created_at': u.created_at.strftime('%d/%m/%Y %H:%M') if u.created_at else '',
            'last_login': u.last_login.strftime('%d/%m/%Y %H:%M') if u.last_login else 'Nunca',
            'departamento': u.preset.departamento_formato if u.preset else '',
            'jefe': u.preset.jefe_directo_nombre if u.preset else '',
            'empresa': empresa,
        })
    return jsonify({'success': True, 'users': result, 'total': len(result)})


@mobper_bp.route('/admin/api/users/<int:user_id>', methods=['GET'])
@mobper_admin_required
def admin_api_get_user(user_id):
    """API: Obtiene detalle de un usuario."""
    u = MobPerUser.query.get_or_404(user_id)
    data = {
        'id': u.id,
        'numero_socio': u.numero_socio,
        'nombre_completo': u.nombre_completo,
        'is_active': u.is_active,
        'is_admin': u.is_admin,
        'created_at': u.created_at.strftime('%d/%m/%Y %H:%M') if u.created_at else '',
        'last_login': u.last_login.strftime('%d/%m/%Y %H:%M') if u.last_login else 'Nunca',
        'preset': None,
    }
    if u.preset:
        data['preset'] = {
            'nombre_formato': u.preset.nombre_formato or '',
            'departamento_formato': u.preset.departamento_formato or '',
            'jefe_directo_nombre': u.preset.jefe_directo_nombre or '',
            'hora_entrada_default': u.preset.hora_entrada_default.strftime('%H:%M') if u.preset.hora_entrada_default else '09:00',
            'tolerancia_segundos': u.preset.tolerancia_segundos or 600,
        }
    return jsonify({'success': True, 'user': data})


@mobper_bp.route('/admin/api/users/<int:user_id>', methods=['PUT'])
@mobper_admin_required
def admin_api_update_user(user_id):
    """API: Actualiza datos de un usuario."""
    current = get_current_mobper_user()
    u = MobPerUser.query.get_or_404(user_id)
    data = request.get_json()

    try:
        if 'nombre_completo' in data and data['nombre_completo'].strip():
            u.nombre_completo = data['nombre_completo'].strip()
        if 'is_active' in data:
            u.is_active = bool(data['is_active'])
        if 'is_admin' in data:
            # No puede quitarse admin a sí mismo
            if u.id != current.id:
                u.is_admin = bool(data['is_admin'])
        if 'password' in data and data['password'].strip():
            u.set_password(data['password'].strip())

        # Actualizar preset si viene
        if 'preset' in data and u.preset:
            p = u.preset
            if 'nombre_formato' in data['preset']:
                p.nombre_formato = data['preset']['nombre_formato']
            if 'departamento_formato' in data['preset']:
                p.departamento_formato = data['preset']['departamento_formato']
            if 'jefe_directo_nombre' in data['preset']:
                p.jefe_directo_nombre = data['preset']['jefe_directo_nombre']

        db.session.commit()
        return jsonify({'success': True, 'message': f'Usuario {u.numero_socio} actualizado correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@mobper_bp.route('/admin/api/users/<int:user_id>', methods=['DELETE'])
@mobper_admin_required
def admin_api_delete_user(user_id):
    """API: Elimina un usuario y todos sus datos."""
    current = get_current_mobper_user()
    u = MobPerUser.query.get_or_404(user_id)

    if u.id == current.id:
        return jsonify({'success': False, 'error': 'No puedes eliminar tu propia cuenta'}), 400

    try:
        nombre = u.nombre_completo
        numero = u.numero_socio
        db.session.delete(u)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Usuario {numero} - {nombre} eliminado'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@mobper_bp.route('/admin/api/users/<int:user_id>/toggle-active', methods=['POST'])
@mobper_admin_required
def admin_api_toggle_active(user_id):
    """API: Activa o desactiva un usuario."""
    current = get_current_mobper_user()
    u = MobPerUser.query.get_or_404(user_id)

    if u.id == current.id:
        return jsonify({'success': False, 'error': 'No puedes desactivar tu propia cuenta'}), 400

    try:
        u.is_active = not u.is_active
        db.session.commit()
        estado = 'activado' if u.is_active else 'desactivado'
        return jsonify({'success': True, 'is_active': u.is_active, 'message': f'Usuario {estado}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@mobper_bp.route('/admin/api/users/<int:user_id>/toggle-admin', methods=['POST'])
@mobper_admin_required
def admin_api_toggle_admin(user_id):
    """API: Otorga o revoca permisos de admin."""
    current = get_current_mobper_user()
    u = MobPerUser.query.get_or_404(user_id)

    if u.id == current.id:
        return jsonify({'success': False, 'error': 'No puedes modificar tu propio rol'}), 400

    try:
        u.is_admin = not u.is_admin
        db.session.commit()
        rol = 'Admin' if u.is_admin else 'Usuario'
        return jsonify({'success': True, 'is_admin': u.is_admin, 'message': f'Rol cambiado a {rol}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@mobper_bp.route('/admin/api/users/<int:user_id>/reset-password', methods=['POST'])
@mobper_admin_required
def admin_api_reset_password(user_id):
    """API: Resetea la contraseña de un usuario."""
    u = MobPerUser.query.get_or_404(user_id)
    data = request.get_json()
    nueva = data.get('password', '').strip()

    if len(nueva) < 4:
        return jsonify({'success': False, 'error': 'La contraseña debe tener al menos 4 caracteres'}), 400

    try:
        u.set_password(nueva)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Contraseña de {u.numero_socio} actualizada'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# DASHBOARD GRUPAL - GESTIÓN DE EQUIPO
# =============================================================================

def get_group_members(leader_user):
    """
    Obtiene los miembros del grupo de un líder.
    SIMULACIÓN: Por ahora, todos los usuarios registrados pertenecen al grupo del admin.
    En producción, esto se filtrará por relación jefe-empleado.
    """
    members = MobPerUser.query.filter(
        MobPerUser.id != leader_user.id,
        MobPerUser.is_active == True
    ).order_by(MobPerUser.nombre_completo).all()
    return members


def calcular_resumen_miembro(user, quincena):
    """Calcula el resumen de incidencias de un miembro para una quincena."""
    try:
        incidencias = calcular_incidencias_quincena(user, quincena)
        a_tiempo = sum(1 for i in incidencias if i['estado_auto'] == 'A_TIEMPO')
        retardos = sum(1 for i in incidencias if i['estado_auto'] == 'RETARDO')
        faltas = sum(1 for i in incidencias if i['estado_auto'] == 'FALTA')
        inhabiles = sum(1 for i in incidencias if i['estado_auto'] == 'INHABIL')
        descansos = sum(1 for i in incidencias if i['estado_auto'] == 'DESCANSO')
        faltas_sin_clasificar = sum(
            1 for i in incidencias
            if i['estado_auto'] == 'FALTA' and not i.get('clasificacion')
        )
        if faltas_sin_clasificar > 0:
            estado = 'pendiente'
        elif faltas > 0 or retardos > 2:
            estado = 'alerta'
        else:
            estado = 'ok'
        return {
            'a_tiempo': a_tiempo, 'retardos': retardos, 'faltas': faltas,
            'inhabiles': inhabiles, 'descansos': descansos,
            'faltas_sin_clasificar': faltas_sin_clasificar,
            'estado': estado, 'incidencias': incidencias,
        }
    except Exception as e:
        print(f"[GRUPO] Error calculando resumen de {user.numero_socio}: {e}")
        return {
            'a_tiempo': 0, 'retardos': 0, 'faltas': 0,
            'inhabiles': 0, 'descansos': 0,
            'faltas_sin_clasificar': 0, 'estado': 'error', 'incidencias': [],
        }


@mobper_bp.route('/grupo')
@mobper_admin_required
def grupo_dashboard():
    """Dashboard de gestión grupal."""
    current_user = get_current_mobper_user()
    return render_template('mobper_grupo.html', current_user=current_user)


@mobper_bp.route('/grupo/api/resumen', methods=['GET'])
@mobper_admin_required
def grupo_api_resumen():
    """API: Resumen completo del grupo para una quincena."""
    t_start = time_module.time()
    leader = get_current_mobper_user()
    members = get_group_members(leader)

    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    quincena_num = request.args.get('quincena_num', type=int)

    if year and month and quincena_num:
        quincena = calcular_quincena(year, month, quincena_num)
    else:
        quincena = calcular_quincena_actual()

    quincena_ant = obtener_quincena_anterior(quincena)
    quincena_sig = obtener_quincena_siguiente(quincena)

    miembros_data = []
    totals = {'a_tiempo': 0, 'retardos': 0, 'faltas': 0, 'pendientes': 0}

    for m in members:
        resumen = calcular_resumen_miembro(m, quincena)
        preset = PresetUsuario.query.filter_by(user_id=m.id).first()
        miembros_data.append({
            'id': m.id,
            'numero_socio': m.numero_socio,
            'nombre_completo': m.nombre_completo,
            'departamento': preset.departamento_formato if preset else '',
            'a_tiempo': resumen['a_tiempo'],
            'retardos': resumen['retardos'],
            'faltas': resumen['faltas'],
            'faltas_sin_clasificar': resumen['faltas_sin_clasificar'],
            'inhabiles': resumen['inhabiles'],
            'descansos': resumen['descansos'],
            'estado': resumen['estado'],
            'last_login': m.last_login.strftime('%d/%m/%Y %H:%M') if m.last_login else 'Nunca',
        })
        totals['a_tiempo'] += resumen['a_tiempo']
        totals['retardos'] += resumen['retardos']
        totals['faltas'] += resumen['faltas']
        if resumen['faltas_sin_clasificar'] > 0:
            totals['pendientes'] += 1

    elapsed = time_module.time() - t_start
    print(f"[GRUPO] Resumen calculado en {elapsed:.2f}s para {len(members)} miembros")

    from datetime import date as date_cls
    hoy = date_cls.today()
    puede_ir_siguiente = quincena_sig['inicio'] <= hoy

    return jsonify({
        'success': True,
        'quincena': {
            'nombre': quincena['nombre'],
            'anio': quincena['anio'],
            'mes': quincena['mes'],
            'numero': quincena['numero'],
        },
        'nav': {
            'ant': {'anio': quincena_ant['anio'], 'mes': quincena_ant['mes'], 'numero': quincena_ant['numero']},
            'sig': {'anio': quincena_sig['anio'], 'mes': quincena_sig['mes'], 'numero': quincena_sig['numero']},
            'puede_sig': puede_ir_siguiente,
        },
        'miembros': miembros_data,
        'totals': totals,
        'total_miembros': len(members),
        'elapsed': round(elapsed, 2),
    })


@mobper_bp.route('/grupo/api/miembro/<int:user_id>/detalle', methods=['GET'])
@mobper_admin_required
def grupo_api_miembro_detalle(user_id):
    """API: Detalle de incidencias de un miembro para una quincena."""
    user = MobPerUser.query.get_or_404(user_id)
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    quincena_num = request.args.get('quincena_num', type=int)

    if year and month and quincena_num:
        quincena = calcular_quincena(year, month, quincena_num)
    else:
        quincena = calcular_quincena_actual()

    incidencias = calcular_incidencias_quincena(user, quincena)
    preset = PresetUsuario.query.filter_by(user_id=user.id).first()

    inc_list = []
    for inc in incidencias:
        inc_list.append({
            'fecha': inc['fecha'].isoformat(),
            'dia_semana': inc['dia_semana'],
            'tipo_dia': inc['tipo_dia'],
            'estado_auto': inc['estado_auto'],
            'minutos_diferencia': inc['minutos_diferencia'],
            'primer_registro': inc['primer_registro'].strftime('%H:%M:%S') if inc['primer_registro'] else None,
            'hora_limite': inc['hora_limite'].strftime('%H:%M') if inc.get('hora_limite') else None,
            'clasificacion': inc.get('clasificacion'),
            'justificado': inc.get('justificado', True),
            'nombre_inhabil': inc.get('nombre_inhabil'),
        })

    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'numero_socio': user.numero_socio,
            'nombre_completo': user.nombre_completo,
            'departamento': preset.departamento_formato if preset else '',
        },
        'quincena': quincena['nombre'],
        'incidencias': inc_list,
    })


@mobper_bp.route('/grupo/api/generar-excel/<int:user_id>', methods=['GET'])
@mobper_admin_required
def grupo_api_generar_excel_miembro(user_id):
    """API: Genera Excel de un miembro específico."""
    try:
        from webapp.mobper_excel import generar_formato_excel
        user = MobPerUser.query.get_or_404(user_id)
        preset = PresetUsuario.query.filter_by(user_id=user.id).first()
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        quincena_num = request.args.get('quincena_num', type=int)
        con_goce = request.args.get('con_goce', '1') == '1'

        if year and month and quincena_num:
            quincena = calcular_quincena(year, month, quincena_num)
        else:
            quincena = calcular_quincena_actual()

        incidencias = calcular_incidencias_quincena(user, quincena)
        output_path, filename = generar_formato_excel(
            user=user, preset=preset, incidencias=incidencias,
            quincena=quincena, con_goce=con_goce
        )

        @after_this_request
        def remove_file_grupo_single(response):
            try:
                os.remove(output_path)
            except Exception:
                pass
            return response

        return send_file(
            output_path, as_attachment=True, download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@mobper_bp.route('/grupo/api/generar-excel-todos', methods=['GET'])
@mobper_admin_required
def grupo_api_generar_excel_todos():
    """API: Genera un ZIP con los Excel de todos los miembros del grupo."""
    import zipfile
    import tempfile
    try:
        from webapp.mobper_excel import generar_formato_excel
        leader = get_current_mobper_user()
        members = get_group_members(leader)
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        quincena_num = request.args.get('quincena_num', type=int)
        con_goce = request.args.get('con_goce', '1') == '1'

        if year and month and quincena_num:
            quincena = calcular_quincena(year, month, quincena_num)
        else:
            quincena = calcular_quincena_actual()

        zip_dir = tempfile.mkdtemp()
        zip_path = os.path.join(zip_dir, 'MovPer_Grupo.zip')
        generated_files = []

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for m in members:
                try:
                    preset = PresetUsuario.query.filter_by(user_id=m.id).first()
                    incidencias = calcular_incidencias_quincena(m, quincena)
                    output_path, filename = generar_formato_excel(
                        user=m, preset=preset, incidencias=incidencias,
                        quincena=quincena, con_goce=con_goce
                    )
                    zf.write(output_path, filename)
                    generated_files.append(output_path)
                except Exception as e:
                    print(f"[GRUPO ZIP] Error con {m.nombre_completo}: {e}")

        for fp in generated_files:
            try:
                os.remove(fp)
            except Exception:
                pass

        @after_this_request
        def cleanup_grupo_zip(response):
            try:
                os.remove(zip_path)
                os.rmdir(zip_dir)
            except Exception:
                pass
            return response

        q_name = quincena['nombre'].replace(' ', '_')
        return send_file(
            zip_path, as_attachment=True,
            download_name=f'MovPer_Grupo_{q_name}.zip',
            mimetype='application/zip'
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
