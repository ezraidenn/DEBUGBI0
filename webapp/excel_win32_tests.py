"""
Módulo de prueba FINAL para Excel usando WIN32COM.
Incluye múltiples escenarios de prueba con control de círculos/shapes.

MAPEO DE CELDAS:
- E8: Nombre del empleado
- Q8: Departamento (ej: "TI")
- H10: Fecha de Autorización
- P10: Fecha de Aplicación (días)
- G20: Motivo
- E56: Nombre del que Solicitó (empleado)
- J56: Nombre del que Autorizó (jefe)

SHAPES (Círculos de opciones):
- Shape #1 (C15): PARA FALTAR
- Shape #2 (C16): PARA SALIR Y REGRESAR
- Shape #3 (M16): OLVIDO CHECAR TARJETA
- Shape #4 (L14): PARA RETIRARSE TEMPRANO
- Shape #5 (C17): PARA LLEGAR TARDE
- Shape #9 (P17): GOCE SUELDO SI
- Shape #10 (R17): GOCE SUELDO NO

COLORES:
- Negro (seleccionado): RGB(0, 0, 0)
- Blanco (no seleccionado): RGB(255, 255, 255)
"""

import os
import shutil
from datetime import datetime, date
import win32com.client as win32

# Rutas
TEMPLATE_PATH = r"C:\Users\raulc\Downloads\debug biostar para checadores\modulo mobper\F-RH-18-MIT-FORMATO-DE-MOVIMIENTO-DE-PERSONAL-3(1).xlsx"
OUTPUT_DIR = r"C:\Users\raulc\Downloads\debug biostar para checadores\webapp\output\excel_tests"

# Mapeo de shapes
SHAPES = {
    'para_faltar': 1,           # C15
    'para_salir_regresar': 2,   # C16
    'olvido_checar': 3,         # M16
    'retirarse_temprano': 4,    # L14
    'para_llegar_tarde': 5,     # C17
    'goce_sueldo_si': 9,        # P17
    'goce_sueldo_no': 10,       # R17
}

# Convertir RGB a formato Excel (BGR)
def rgb_to_excel(r, g, b):
    return r + (g << 8) + (b << 16)

COLOR_NEGRO = rgb_to_excel(0, 0, 0)
COLOR_BLANCO = rgb_to_excel(255, 255, 255)

def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_output_path(test_name):
    ensure_output_dir()
    timestamp = datetime.now().strftime('%H%M%S')
    return os.path.join(OUTPUT_DIR, f"{test_name}_{timestamp}.xlsx")


def set_circle_color(ws, shape_index, is_selected):
    """Establecer el color de un círculo (negro=seleccionado, blanco=no)."""
    try:
        shape = ws.Shapes(shape_index)
        if is_selected:
            shape.Fill.ForeColor.RGB = COLOR_NEGRO
            shape.Fill.Visible = True
        else:
            shape.Fill.ForeColor.RGB = COLOR_BLANCO
            shape.Fill.Visible = False  # Solo contorno
    except Exception as e:
        print(f"  Error en shape {shape_index}: {e}")


def fill_mobper_form(ws, data):
    """
    Llenar el formulario de MobPer con los datos proporcionados.
    
    data dict keys:
    - nombre: str
    - departamento: str
    - fecha_autorizacion: str o date
    - fecha_aplicacion: str (días)
    - motivo: str
    - nombre_solicito: str (empleado)
    - nombre_autorizo: str (jefe)
    - para_faltar: bool
    - para_llegar_tarde: bool
    - para_salir_regresar: bool
    - olvido_checar: bool
    - retirarse_temprano: bool
    - goce_sueldo: bool (True=Si, False=No)
    """
    
    # Celdas de texto
    if data.get('nombre'):
        ws.Range('E8').Value = data['nombre']
    
    if data.get('departamento'):
        ws.Range('Q8').Value = data['departamento']
    
    if data.get('fecha_autorizacion'):
        fecha = data['fecha_autorizacion']
        if isinstance(fecha, (date, datetime)):
            ws.Range('H10').Value = fecha.strftime('%d/%m/%Y')
        else:
            ws.Range('H10').Value = str(fecha)
    
    if data.get('fecha_aplicacion'):
        ws.Range('P10').Value = data['fecha_aplicacion']
    
    if data.get('motivo'):
        ws.Range('G20').Value = data['motivo']
    
    if data.get('nombre_solicito'):
        ws.Range('E56').Value = data['nombre_solicito']
    
    if data.get('nombre_autorizo'):
        ws.Range('J56').Value = data['nombre_autorizo']
    
    # Círculos de opciones
    set_circle_color(ws, SHAPES['para_faltar'], data.get('para_faltar', False))
    set_circle_color(ws, SHAPES['para_salir_regresar'], data.get('para_salir_regresar', False))
    set_circle_color(ws, SHAPES['olvido_checar'], data.get('olvido_checar', False))
    set_circle_color(ws, SHAPES['retirarse_temprano'], data.get('retirarse_temprano', False))
    set_circle_color(ws, SHAPES['para_llegar_tarde'], data.get('para_llegar_tarde', False))
    
    # Goce de sueldo
    goce = data.get('goce_sueldo', True)
    set_circle_color(ws, SHAPES['goce_sueldo_si'], goce)
    set_circle_color(ws, SHAPES['goce_sueldo_no'], not goce)


def generate_excel(test_name, data):
    """Generar un archivo Excel con los datos especificados."""
    result = {
        'test_name': test_name,
        'success': False,
        'output_file': None,
        'error': None
    }
    
    try:
        output_path = get_output_path(test_name)
        shutil.copy(TEMPLATE_PATH, output_path)
        
        excel = win32.gencache.EnsureDispatch('Excel.Application')
        excel.Visible = False
        excel.DisplayAlerts = False
        
        wb = excel.Workbooks.Open(output_path)
        ws = wb.ActiveSheet
        
        fill_mobper_form(ws, data)
        
        wb.Save()
        wb.Close()
        excel.Quit()
        
        result['success'] = True
        result['output_file'] = output_path
        
    except Exception as e:
        result['error'] = str(e)
        try:
            excel.Quit()
        except:
            pass
    
    return result


# ============================================================
# ESCENARIOS DE PRUEBA
# ============================================================

def test_solo_retardo():
    """Prueba: Solo retardos (llegar tarde)."""
    return generate_excel('solo_retardo', {
        'nombre': 'MARIA FERNANDEZ LOPEZ',
        'departamento': 'CONTABILIDAD',
        'fecha_autorizacion': date.today(),
        'fecha_aplicacion': '3, 5, 8 de Febrero',
        'motivo': 'Retardo justificado los dias 3, 5 y 8 de Febrero 2026.',
        'nombre_solicito': 'Maria Fernandez Lopez',
        'nombre_autorizo': 'Pedro Gonzalez Martinez',
        'para_faltar': False,
        'para_llegar_tarde': True,
        'goce_sueldo': True,
    })


def test_solo_falta():
    """Prueba: Solo faltas."""
    return generate_excel('solo_falta', {
        'nombre': 'JUAN CARLOS HERNANDEZ',
        'departamento': 'RECURSOS HUMANOS',
        'fecha_autorizacion': date.today(),
        'fecha_aplicacion': '10, 11, 12 de Febrero',
        'motivo': 'Falta justificada por cita medica los dias 10, 11 y 12 de Febrero.',
        'nombre_solicito': 'Juan Carlos Hernandez',
        'nombre_autorizo': 'Ana Maria Ruiz',
        'para_faltar': True,
        'para_llegar_tarde': False,
        'goce_sueldo': True,
    })


def test_falta_y_retardo():
    """Prueba: Combinación de faltas y retardos."""
    return generate_excel('falta_y_retardo', {
        'nombre': 'ROBERTO MARTINEZ SANCHEZ',
        'departamento': 'TI',
        'fecha_autorizacion': date.today(),
        'fecha_aplicacion': '1, 2, 5, 6, 8, 12, 15 de Febrero',
        'motivo': 'Dias 1, 2 falta justificada (trabajo remoto). Dias 5, 6, 8, 12, 15 retardo justificado.',
        'nombre_solicito': 'Roberto Martinez Sanchez',
        'nombre_autorizo': 'Carlos Medina',
        'para_faltar': True,
        'para_llegar_tarde': True,
        'goce_sueldo': True,
    })


def test_sin_goce_sueldo():
    """Prueba: Falta SIN goce de sueldo."""
    return generate_excel('sin_goce_sueldo', {
        'nombre': 'PATRICIA GOMEZ VILLA',
        'departamento': 'VENTAS',
        'fecha_autorizacion': date.today(),
        'fecha_aplicacion': '20, 21 de Febrero',
        'motivo': 'Asunto personal sin goce de sueldo.',
        'nombre_solicito': 'Patricia Gomez Villa',
        'nombre_autorizo': 'Miguel Angel Torres',
        'para_faltar': True,
        'para_llegar_tarde': False,
        'goce_sueldo': False,  # SIN goce
    })


def test_olvido_checar():
    """Prueba: Olvido checar tarjeta."""
    return generate_excel('olvido_checar', {
        'nombre': 'LUIS ENRIQUE MORALES',
        'departamento': 'OPERACIONES',
        'fecha_autorizacion': date.today(),
        'fecha_aplicacion': '7 de Febrero',
        'motivo': 'Olvido registrar entrada el dia 7 de Febrero.',
        'nombre_solicito': 'Luis Enrique Morales',
        'nombre_autorizo': 'Sofia Ramirez',
        'para_faltar': False,
        'para_llegar_tarde': False,
        'olvido_checar': True,
        'goce_sueldo': True,
    })


def test_retirarse_temprano():
    """Prueba: Salida anticipada."""
    return generate_excel('retirarse_temprano', {
        'nombre': 'ANDREA SILVA MENDEZ',
        'departamento': 'ADMINISTRACION',
        'fecha_autorizacion': date.today(),
        'fecha_aplicacion': '14 de Febrero',
        'motivo': 'Permiso para salir temprano por cita medica.',
        'nombre_solicito': 'Andrea Silva Mendez',
        'nombre_autorizo': 'Ricardo Lopez',
        'para_faltar': False,
        'retirarse_temprano': True,
        'goce_sueldo': True,
    })


def test_formato_quincena_completa():
    """Prueba: Formato de quincena completa con múltiples incidencias."""
    return generate_excel('quincena_completa', {
        'nombre': 'RAUL ABEL CETINA POOL',
        'departamento': 'TI',
        'fecha_autorizacion': date.today(),
        'fecha_aplicacion': '1, 2, 3, 5, 6, 7, 8, 9, 12, 13, 14, 15 de Febrero',
        'motivo': 'Dias 1-2 trabajo remoto (falta just.), Dias 3,5,6,7,8,9,12,15 retardo justificado, Dias 13-14 guardia telefonica.',
        'nombre_solicito': 'Raul Abel Cetina Pool',
        'nombre_autorizo': 'Carlos Medina',
        'para_faltar': True,
        'para_llegar_tarde': True,
        'goce_sueldo': True,
    })


def test_salir_y_regresar():
    """Prueba: Salir y regresar."""
    return generate_excel('salir_regresar', {
        'nombre': 'CARMEN RODRIGUEZ PEREZ',
        'departamento': 'LEGAL',
        'fecha_autorizacion': date.today(),
        'fecha_aplicacion': '6 de Febrero',
        'motivo': 'Permiso para salir a tramite bancario y regresar.',
        'nombre_solicito': 'Carmen Rodriguez Perez',
        'nombre_autorizo': 'Fernando Diaz',
        'para_salir_regresar': True,
        'goce_sueldo': True,
    })


# Lista de todos los tests
ALL_TESTS = [
    ('solo_retardo', test_solo_retardo, 'Solo retardos (llegar tarde)'),
    ('solo_falta', test_solo_falta, 'Solo faltas'),
    ('falta_y_retardo', test_falta_y_retardo, 'Faltas + Retardos combinados'),
    ('sin_goce_sueldo', test_sin_goce_sueldo, 'Falta SIN goce de sueldo'),
    ('olvido_checar', test_olvido_checar, 'Olvido checar tarjeta'),
    ('retirarse_temprano', test_retirarse_temprano, 'Salida anticipada'),
    ('quincena_completa', test_formato_quincena_completa, 'Quincena completa con múltiples incidencias'),
    ('salir_regresar', test_salir_y_regresar, 'Salir y regresar'),
]


def run_all_tests():
    """Ejecutar todos los tests."""
    print("="*60)
    print("TESTS DE GENERACION EXCEL - WIN32COM")
    print("="*60)
    
    results = []
    for test_id, test_func, description in ALL_TESTS:
        print(f"\nEjecutando: {description}...")
        result = test_func()
        results.append(result)
        
        if result['success']:
            print(f"  ✓ OK: {os.path.basename(result['output_file'])}")
        else:
            print(f"  ✗ ERROR: {result['error']}")
    
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    
    ok_count = sum(1 for r in results if r['success'])
    print(f"Exitosos: {ok_count}/{len(results)}")
    
    return results


if __name__ == '__main__':
    run_all_tests()
