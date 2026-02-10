"""
Módulo de generación de formato Excel para MovPer
Usa win32com (pywin32) para llenar el template Excel preservando completamente el formato y shapes.
"""

import win32com.client as win32
from datetime import datetime, date
import os
import shutil
from typing import List, Dict, Tuple
import pythoncom

# Directorio base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuración de rutas
TEMPLATE_PATH = os.path.join(BASE_DIR, 'templates', 'F-RH-18-MIT-FORMATO-DE-MOVIMIENTO-DE-PERSONAL-3(1).xlsx')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output', 'mobper')

# =============================================================================
# MAPEO DE CELDAS DEL TEMPLATE EXCEL
# =============================================================================
# Basado en análisis visual del formato F-RH-18-MIT

CELDAS = {
    # Encabezado - Coordenadas exactas confirmadas por el usuario
    'NOMBRE': 'E8',              # Nombre del empleado (fila 8, columnas E-M)
    'DEPARTAMENTO': 'Q8',        # Departamento (fila 8, columnas Q-R)
    'FECHA_AUTORIZACION': 'H10', # Fecha de autorización (fila 10, columnas H-K)
    'FECHA_APLICACION': 'P10',   # Fechas de aplicación (fila 10, columnas P-R)
    
    # Círculos de tipo de permiso
    'PARA_FALTAR': 'D15',        # Checkbox para faltar (fila 15, columna D)
    'PARA_SALIR_REGRESAR': 'D16', # Checkbox para salir y regresar (fila 16, columna D)
    'PARA_LLEGAR_TARDE': 'D17',  # Checkbox para llegar tarde (fila 17, columna D)
    'PARA_RETIRARSE': 'M15',     # Checkbox retirarse temprano (fila 15, columna M)
    'OLVIDO_CHECAR': 'M16',      # Checkbox olvidó checar (fila 16, columna M)
    
    # Goce de sueldo (necesitaría confirmar columnas exactas)
    'GOCE_SI': 'F17',            # Círculo SI
    'GOCE_NO': 'G17',            # Círculo NO
    
    # Motivo
    'MOTIVO': 'G20',             # Campo de motivo (filas 20-21, columnas G-R)
    
    # Firmas
    'SOLICITO_NOMBRE': 'E56',    # Nombre del solicitante (fila 56, columnas E-G)
    'AUTORIZO_NOMBRE': 'J56',    # Nombre del autorizador/jefe (fila 56, columna J)
    'RECIBIO_NOMBRE': 'Q56',     # "Recursos Humanos" (fila 56, estimado)
}

# =============================================================================
# MAPEO DE SHAPES (CÍRCULOS) DEL TEMPLATE
# =============================================================================
# Basado en análisis con win32com - índices de shapes

SHAPES = {
    'PARA_FALTAR': 1,           # Shape #1 en C15
    'PARA_SALIR_REGRESAR': 2,   # Shape #2 en C16
    'OLVIDO_CHECAR': 3,         # Shape #3 en M16
    'PARA_RETIRARSE': 4,        # Shape #4 en L14
    'PARA_LLEGAR_TARDE': 5,     # Shape #5 en C17
    'GOCE_SI': 9,               # Shape #9 en P17
    'GOCE_NO': 10,              # Shape #10 en R17
}

# Colores RGB para Excel (formato BGR)
def rgb_to_excel(r, g, b):
    return r + (g << 8) + (b << 16)

COLOR_NEGRO = rgb_to_excel(0, 0, 0)
COLOR_BLANCO = rgb_to_excel(255, 255, 255)

# Meses en español
MESES_ES = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
}


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def calcular_tamano_letra(texto: str, max_size: int = 12, min_size: int = 8) -> int:
    """
    Calcula el tamaño de letra óptimo según la longitud del texto.
    
    - Hasta 10 chars: max_size (12)
    - 11-15 chars: 11
    - 16-20 chars: 10
    - 21-25 chars: 9
    - 26+ chars: min_size (8)
    """
    length = len(texto)
    if length <= 10:
        return max_size
    elif length <= 15:
        return 11
    elif length <= 20:
        return 10
    elif length <= 25:
        return 9
    else:
        return min_size


def formatear_fechas_compactas(dias: List[int], mes: str) -> str:
    """
    Formatea los días de forma compacta.
    Si hay más de 4 días, usa formato sin espacios: 1,2,3,5,8
    Si hay 4 o menos, usa espacios: 1, 2, 3, 5
    """
    if len(dias) <= 4:
        dias_str = ', '.join(str(d) for d in sorted(dias))
    else:
        dias_str = ','.join(str(d) for d in sorted(dias))
    
    return f"{dias_str} de {mes}"


def set_circle_color(sheet, shape_index: int, is_selected: bool):
    """
    Establece el color de un círculo/shape.
    Negro = seleccionado, Blanco = no seleccionado.
    """
    try:
        shape = sheet.Shapes(shape_index)
        if is_selected:
            shape.Fill.ForeColor.RGB = COLOR_NEGRO
            shape.Fill.Visible = True
        else:
            shape.Fill.ForeColor.RGB = COLOR_BLANCO
            shape.Fill.Visible = False  # Solo contorno
        print(f"[MOVPER EXCEL] Shape {shape_index}: {'NEGRO' if is_selected else 'BLANCO'}")
    except Exception as e:
        print(f"[MOVPER EXCEL] Error en shape {shape_index}: {e}")


def agrupar_dias_consecutivos(dias: List[int]) -> str:
    """
    Agrupa días consecutivos para mostrar de forma compacta.
    Ejemplo: [1,2,3,5,7,8,9] -> "1-3, 5, 7-9"
    """
    if not dias:
        return ""
    
    dias = sorted(set(dias))
    grupos = []
    inicio = dias[0]
    fin = dias[0]
    
    for dia in dias[1:]:
        if dia == fin + 1:
            fin = dia
        else:
            if inicio == fin:
                grupos.append(str(inicio))
            else:
                grupos.append(f"{inicio}-{fin}" if fin - inicio > 1 else f"{inicio},{fin}")
            inicio = fin = dia
    
    # Agregar último grupo
    if inicio == fin:
        grupos.append(str(inicio))
    else:
        grupos.append(f"{inicio}-{fin}" if fin - inicio > 1 else f"{inicio},{fin}")
    
    return ", ".join(grupos)


def filtrar_incidencias_a_justificar(incidencias: List[Dict]) -> List[Dict]:
    """
    Filtra las incidencias que deben aparecer en el formato MovPer.
    
    Incluye:
    - Retardos que tienen justificado=True (o no definido, por defecto True)
    - Faltas que tienen clasificacion (REMOTO, GUARDIA, PERMISO, VACACIONES) 
      EXCEPTO INCAPACIDAD (las incapacidades no van en MovPer)
    
    Excluye:
    - A_TIEMPO, INHABIL, DESCANSO
    - Retardos con justificado=False
    - Faltas sin clasificar
    - Faltas clasificadas como INCAPACIDAD
    """
    justificadas = []
    
    for inc in incidencias:
        estado_auto = inc.get('estado_auto', '')
        clasificacion = inc.get('clasificacion', '')
        justificado = inc.get('justificado', True)  # Por defecto True
        
        # Retardos: solo los justificados
        if estado_auto == 'RETARDO' and justificado:
            justificadas.append(inc)
        
        # Faltas: solo las clasificadas (excepto INCAPACIDAD)
        elif estado_auto == 'FALTA' and clasificacion:
            if clasificacion != 'INCAPACIDAD':
                justificadas.append(inc)
    
    return justificadas


def generar_formato_excel(
    user,
    preset,
    incidencias: List[Dict],
    quincena: Dict,
    con_goce: bool = True
) -> Tuple[str, str]:
    """
    Genera el formato de movimiento de personal editando la plantilla Excel.
    
    Args:
        user: MovPerUser - Usuario actual
        preset: PresetUsuario - Configuración del usuario
        incidencias: List[Dict] - Lista de incidencias clasificadas
        quincena: Dict - Info de la quincena {inicio, fin, nombre}
        con_goce: bool - Si es con goce de sueldo
    
    Returns:
        Tuple[str, str]: (ruta_archivo, nombre_archivo)
    """
    
    # Crear directorio de salida si no existe
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generar nombre de archivo único
    fecha_str = quincena['inicio'].strftime('%Y%m%d')
    output_filename = f"MovPer_{user.numero_socio}_{fecha_str}.xlsx"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    print(f"[MOVPER EXCEL] Iniciando generación de Excel con win32com")
    print(f"[MOVPER EXCEL] Template: {TEMPLATE_PATH}")
    print(f"[MOVPER EXCEL] Output: {output_path}")
    print(f"[MOVPER EXCEL] Usuario: {user.nombre_completo}")
    print(f"[MOVPER EXCEL] Incidencias: {len(incidencias)}")
    
    # IMPORTANTE: Copiar template PRIMERO, luego abrir la copia
    print(f"[MOVPER EXCEL] Copiando template a output...")
    shutil.copy(TEMPLATE_PATH, output_path)
    
    # Inicializar COM
    pythoncom.CoInitialize()
    
    # Usar gencache.EnsureDispatch (más estable que Dispatch)
    excel = win32.gencache.EnsureDispatch('Excel.Application')
    excel.Visible = False  # NO mostrar Excel
    excel.DisplayAlerts = False
    
    try:
        # Abrir la COPIA (no el template original)
        wb = excel.Workbooks.Open(os.path.abspath(output_path))
        sheet = wb.ActiveSheet
        print(f"[MOVPER EXCEL] Archivo abierto con win32com")
        
        # =============================================================
        # FILTRAR INCIDENCIAS QUE VAN A JUSTIFICARSE
        # =============================================================
        # Solo incluir: retardos justificados + faltas clasificadas (excepto INCAPACIDAD)
        incidencias_justificadas = filtrar_incidencias_a_justificar(incidencias)
        print(f"[MOVPER EXCEL] Incidencias totales: {len(incidencias)}")
        print(f"[MOVPER EXCEL] Incidencias a justificar: {len(incidencias_justificadas)}")
        
        # =============================================================
        # LLENAR DATOS DEL ENCABEZADO
        # =============================================================
        
        # Nombre del empleado
        nombre = preset.nombre_formato if preset and preset.nombre_formato else user.nombre_completo
        print(f"[MOVPER EXCEL] Escribiendo nombre en {CELDAS['NOMBRE']}: {nombre}")
        sheet.Range(CELDAS['NOMBRE']).Value = nombre.upper()
        
        # Departamento con tamaño de letra dinámico
        departamento = preset.departamento_formato if preset and preset.departamento_formato else "Sin departamento"
        print(f"[MOVPER EXCEL] Escribiendo departamento en {CELDAS['DEPARTAMENTO']}: {departamento}")
        sheet.Range(CELDAS['DEPARTAMENTO']).Value = departamento.upper()
        # Ajustar tamaño de letra según longitud
        tamano_depto = calcular_tamano_letra(departamento, max_size=12, min_size=8)
        sheet.Range(CELDAS['DEPARTAMENTO']).Font.Size = tamano_depto
        print(f"[MOVPER EXCEL] Tamaño letra departamento: {tamano_depto}")
        
        # Fecha de autorización (hoy) en formato dd-mmm-yy con mes en español
        now = datetime.now()
        mes_corto = {1:'ene',2:'feb',3:'mar',4:'abr',5:'may',6:'jun',7:'jul',8:'ago',9:'sep',10:'oct',11:'nov',12:'dic'}
        fecha_auth = f"{now.day:02d}-{mes_corto[now.month]}-{now.strftime('%y')}"
        print(f"[MOVPER EXCEL] Escribiendo fecha auth en {CELDAS['FECHA_AUTORIZACION']}: {fecha_auth}")
        sheet.Range(CELDAS['FECHA_AUTORIZACION']).Value = fecha_auth
        
        # Fecha de aplicación (días del periodo) con tamaño dinámico
        dias_periodo = construir_fechas_aplicacion(incidencias_justificadas, quincena)
        print(f"[MOVPER EXCEL] Escribiendo fechas aplicación en {CELDAS['FECHA_APLICACION']}: {dias_periodo}")
        sheet.Range(CELDAS['FECHA_APLICACION']).Value = dias_periodo
        # Ajustar tamaño según longitud
        tamano_fechas = calcular_tamano_letra(dias_periodo, max_size=12, min_size=8)
        sheet.Range(CELDAS['FECHA_APLICACION']).Font.Size = tamano_fechas
        print(f"[MOVPER EXCEL] Tamaño letra fechas: {tamano_fechas}")
        
        # =============================================================
        # ANALIZAR TIPOS DE INCIDENCIAS Y MARCAR CÍRCULOS REALES
        # =============================================================
        
        tipos = analizar_tipos_incidencias(incidencias_justificadas)
        
        # Primero, poner todos los círculos en blanco (no seleccionado)
        print(f"[MOVPER EXCEL] Reseteando todos los círculos a blanco...")
        for shape_name, shape_idx in SHAPES.items():
            set_circle_color(sheet, shape_idx, False)
        
        # Marcar los círculos correspondientes según tipos encontrados
        print(f"[MOVPER EXCEL] Marcando círculos según incidencias...")
        # PARA FALTAR: cualquier tipo de falta (genérica, remoto, guardia, permiso, vacaciones)
        tiene_faltas = tipos['faltas'] or tipos['remotos'] or tipos['guardias'] or tipos['permisos'] or tipos['vacaciones']
        if tiene_faltas:
            set_circle_color(sheet, SHAPES['PARA_FALTAR'], True)
        if tipos['retardos']:
            set_circle_color(sheet, SHAPES['PARA_LLEGAR_TARDE'], True)
        if tipos['salir_regresar']:
            set_circle_color(sheet, SHAPES['PARA_SALIR_REGRESAR'], True)
        if tipos['olvido_checar']:
            set_circle_color(sheet, SHAPES['OLVIDO_CHECAR'], True)
        if tipos['retirarse_temprano']:
            set_circle_color(sheet, SHAPES['PARA_RETIRARSE'], True)
        
        # Goce de sueldo
        if con_goce:
            set_circle_color(sheet, SHAPES['GOCE_SI'], True)
            set_circle_color(sheet, SHAPES['GOCE_NO'], False)
        else:
            set_circle_color(sheet, SHAPES['GOCE_SI'], False)
            set_circle_color(sheet, SHAPES['GOCE_NO'], True)
        
        # =============================================================
        # GENERAR TEXTO DEL MOTIVO
        # =============================================================
        
        motivo = generar_texto_motivo(incidencias_justificadas, tipos)
        print(f"[MOVPER EXCEL] Escribiendo motivo en {CELDAS['MOTIVO']}: {motivo[:50]}...")
        sheet.Range(CELDAS['MOTIVO']).Value = motivo
        
        # =============================================================
        # FIRMAS
        # =============================================================
        
        # Solicitó (el empleado)
        print(f"[MOVPER EXCEL] Escribiendo solicitó en {CELDAS['SOLICITO_NOMBRE']}: {nombre}")
        sheet.Range(CELDAS['SOLICITO_NOMBRE']).Value = nombre
        
        # Autorizó (jefe directo)
        jefe = preset.jefe_directo_nombre if preset and preset.jefe_directo_nombre else "PENDIENTE"
        print(f"[MOVPER EXCEL] Escribiendo autorizó en {CELDAS['AUTORIZO_NOMBRE']}: {jefe}")
        sheet.Range(CELDAS['AUTORIZO_NOMBRE']).Value = jefe
        
        # Recibió (RH)
        print(f"[MOVPER EXCEL] Escribiendo recibió en {CELDAS['RECIBIO_NOMBRE']}: Recursos Humanos")
        sheet.Range(CELDAS['RECIBIO_NOMBRE']).Value = "Recursos Humanos"
        
        # =============================================================
        # GUARDAR Y CERRAR
        # =============================================================
        
        print(f"[MOVPER EXCEL] Guardando archivo...")
        wb.Save()
        
        print(f"[MOVPER EXCEL] Cerrando workbook...")
        wb.Close(SaveChanges=False)  # Ya guardamos con Save()
        
        print(f"[MOVPER EXCEL] Archivo guardado exitosamente: {output_path}")
        print(f"[MOVPER EXCEL] Verificando que el archivo existe...")
        if os.path.exists(output_path):
            print(f"[MOVPER EXCEL] ✓ Archivo confirmado: {os.path.getsize(output_path)} bytes")
        else:
            print(f"[MOVPER EXCEL] ✗ ERROR: Archivo no existe después de guardar")
        
    except Exception as e:
        print(f"[MOVPER EXCEL] ERROR durante generación: {e}")
        import traceback
        traceback.print_exc()
        try:
            wb.Close(SaveChanges=False)
        except:
            pass
        raise
    finally:
        print(f"[MOVPER EXCEL] Cerrando Excel...")
        excel.Quit()
        pythoncom.CoUninitialize()
        print(f"[MOVPER EXCEL] Excel cerrado")
    
    return output_path, output_filename


def construir_fechas_aplicacion(incidencias: List[Dict], quincena: Dict) -> str:
    """
    Construye la cadena de fechas de aplicación.
    Formato compacto: sin espacios si hay más de 4 días.
    Ejemplo con pocos días: "3, 5, 8 de febrero"
    Ejemplo con muchos días: "1,2,3,5,6,7,8,9,12,15 de febrero"
    """
    if not incidencias:
        return ""
    
    # Extraer días únicos
    dias = sorted(set(inc['fecha'].day for inc in incidencias if inc.get('fecha')))
    mes = quincena['inicio'].month
    mes_nombre = MESES_ES.get(mes, '')
    
    # Formato compacto: sin espacios si hay más de 4 días
    if len(dias) <= 4:
        dias_str = ', '.join(str(d) for d in dias)
    else:
        dias_str = ','.join(str(d) for d in dias)
    
    return f"{dias_str} de {mes_nombre}"


def analizar_tipos_incidencias(incidencias: List[Dict]) -> Dict:
    """
    Analiza las incidencias y agrupa por tipo.
    Usa estado_auto para retardos y clasificacion para faltas.
    Las faltas se agrupan por su clasificación específica (REMOTO, GUARDIA, etc.)
    """
    tipos = {
        'faltas': [],           # Faltas sin clasificar o clasificadas como FALTA genérica
        'retardos': [],
        'remotos': [],          # Faltas clasificadas como TRABAJO_REMOTO/REMOTO
        'guardias': [],         # Faltas clasificadas como GUARDIA/GUARDIA_TELEFONICA
        'permisos': [],         # Faltas clasificadas como PERMISO
        'vacaciones': [],       # Faltas clasificadas como VACACIONES
        'incapacidades': [],    # Faltas clasificadas como INCAPACIDAD (no se usa en motivo)
        'olvido_checar': [],
        'salir_regresar': [],
        'retirarse_temprano': [],
    }
    
    for inc in incidencias:
        estado_auto = inc.get('estado_auto', '')
        clasificacion = inc.get('clasificacion', '')
        fecha = inc.get('fecha')
        dia = fecha.day if fecha else 0
        
        if estado_auto == 'RETARDO':
            tipos['retardos'].append(dia)
        elif estado_auto == 'FALTA':
            # Agrupar faltas por su clasificación específica
            if clasificacion in ('REMOTO', 'TRABAJO_REMOTO'):
                tipos['remotos'].append(dia)
            elif clasificacion in ('GUARDIA', 'GUARDIA_TELEFONICA'):
                tipos['guardias'].append(dia)
            elif clasificacion == 'PERMISO':
                tipos['permisos'].append(dia)
            elif clasificacion == 'VACACIONES':
                tipos['vacaciones'].append(dia)
            elif clasificacion == 'INCAPACIDAD':
                tipos['incapacidades'].append(dia)
            else:
                tipos['faltas'].append(dia)
    
    return tipos


def generar_texto_motivo(incidencias: List[Dict], tipos: Dict) -> str:
    """
    Genera el texto del motivo agrupando por tipo.
    Cada categoría es independiente y no se mezcla.
    
    Ejemplo: "1,2,3,4,5,6 retardo justificado. 7 falta justificada, trabajo remoto. 
              8 falta justificada, guardia telefónico."
    """
    partes = []
    
    # Retardos justificados
    if tipos['retardos']:
        dias_str = agrupar_dias_consecutivos(tipos['retardos'])
        partes.append(f"{dias_str} retardo justificado")
    
    # Faltas genéricas (sin clasificación específica)
    if tipos['faltas']:
        dias_str = agrupar_dias_consecutivos(tipos['faltas'])
        partes.append(f"{dias_str} falta justificada")
    
    # Faltas por trabajo remoto
    if tipos['remotos']:
        dias_str = agrupar_dias_consecutivos(tipos['remotos'])
        partes.append(f"{dias_str} falta justificada, trabajo remoto")
    
    # Faltas por guardia telefónica
    if tipos['guardias']:
        dias_str = agrupar_dias_consecutivos(tipos['guardias'])
        partes.append(f"{dias_str} falta justificada, guardia telefónico")
    
    # Faltas por permiso
    if tipos['permisos']:
        dias_str = agrupar_dias_consecutivos(tipos['permisos'])
        partes.append(f"{dias_str} falta justificada, permiso")
    
    # Faltas por vacaciones
    if tipos['vacaciones']:
        dias_str = agrupar_dias_consecutivos(tipos['vacaciones'])
        partes.append(f"{dias_str} falta justificada, vacaciones")
    
    # NOTA: Incapacidades NO se incluyen en el motivo del MobPer
    
    return ". ".join(partes) + "." if partes else ""


def marcar_circulo_activo(sheet, nombre_celda: str):
    """
    Marca un círculo como activo en el Excel.
    Los círculos en el template son shapes; por ahora marcamos con ●
    """
    if nombre_celda in CELDAS:
        # Nota: En el template real, aquí se manipularía el shape
        # Por ahora dejamos sin cambios ya que los shapes ya existen
        pass


def excel_to_html_preview(excel_path: str) -> str:
    """
    Convierte un archivo Excel a HTML para vista previa en navegador.
    Usa openpyxl para leer los datos.
    
    Returns:
        str: Contenido HTML del Excel
    """
    return generar_html_preview_fallback(excel_path, "")


def generar_html_preview_fallback(excel_path: str, error_msg: str = "") -> str:
    """
    Genera un preview HTML básico.
    Usa openpyxl para leer los datos.
    """
    try:
        from openpyxl import load_workbook
        
        wb = load_workbook(excel_path)
        ws = wb.active
        
        html = ['<style>']
        html.append('table { border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; }')
        html.append('td, th { border: 1px solid #ddd; padding: 8px; text-align: left; }')
        html.append('th { background: #5D4037; color: white; }')
        html.append('tr:nth-child(even) { background: #f9f9f9; }')
        html.append('.merged { font-weight: bold; }')
        html.append('</style>')
        html.append('<table>')
        
        for row in ws.iter_rows(min_row=1, max_row=40, max_col=10):
            html.append('<tr>')
            for cell in row:
                value = cell.value if cell.value else ''
                html.append(f'<td>{value}</td>')
            html.append('</tr>')
        
        html.append('</table>')
        
        if error_msg:
            html.append(f'<p style="color: #888; font-size: 12px; margin-top: 20px;">Nota: Vista simplificada. {error_msg}</p>')
        
        return '\n'.join(html)
        
    except Exception as e:
        return f'<div style="padding: 20px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px;"><strong>Error al generar vista previa:</strong><br>{error_msg}<br><br>Error adicional: {str(e)}</div>'


def obtener_formatos_generados(user_id: int) -> List[Dict]:
    """
    Lista los formatos Excel generados para un usuario.
    """
    archivos = []
    
    if os.path.exists(OUTPUT_DIR):
        for filename in os.listdir(OUTPUT_DIR):
            if filename.endswith('.xlsx'):
                filepath = os.path.join(OUTPUT_DIR, filename)
                stat = os.stat(filepath)
                archivos.append({
                    'filename': filename,
                    'path': filepath,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime)
                })
    
    # Ordenar por fecha de creación (más reciente primero)
    archivos.sort(key=lambda x: x['created'], reverse=True)
    
    return archivos
