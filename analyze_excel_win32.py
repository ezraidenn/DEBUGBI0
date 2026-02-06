"""
Análisis COMPLETO del template Excel - Guarda a archivo directamente.
"""

import win32com.client as win32
import os

TEMPLATE_PATH = r"C:\Users\raulc\Downloads\debug biostar para checadores\modulo mobper\F-RH-18-MIT-FORMATO-DE-MOVIMIENTO-DE-PERSONAL-3(1).xlsx"
OUTPUT_FILE = r"C:\Users\raulc\Downloads\debug biostar para checadores\excel_complete_analysis.txt"

def analyze_complete():
    lines = []
    
    def log(msg):
        print(msg)
        lines.append(msg)
    
    log("="*60)
    log("ANALISIS COMPLETO DEL TEMPLATE (via win32com)")
    log("="*60)
    
    excel = win32.gencache.EnsureDispatch('Excel.Application')
    excel.Visible = False
    excel.DisplayAlerts = False
    
    wb = excel.Workbooks.Open(TEMPLATE_PATH)
    ws = wb.ActiveSheet
    
    # 1. Celdas específicas que nos interesan
    log("\n--- CELDAS IMPORTANTES ---")
    
    important_cells = [
        ('E8', 'Nombre'),
        ('O8', 'Departamento (arriba)'),
        ('H10', 'Fecha Autorizacion'),
        ('P10', 'Fecha Aplicacion'),
        ('G20', 'Motivo'),
        ('F27', 'Departamento (modificaciones)'),
        ('C56', 'Nombre Solicitó'),
        ('G56', 'Nombre Autorizó'),
        ('L56', 'Nombre Recibió'),
    ]
    
    for cell, desc in important_cells:
        val = ws.Range(cell).Value
        log(f"  {cell} ({desc}): '{val}'")
    
    # 2. Buscar donde dice TI (departamento real)
    log("\n--- BUSCANDO 'TI' EN CELDAS ---")
    for row in range(1, 15):
        for col in range(1, 20):
            val = ws.Cells(row, col).Value
            if val and str(val).strip() == 'TI':
                col_letter = chr(64 + col) if col <= 26 else f"Col{col}"
                log(f"  Encontrado 'TI' en: {col_letter}{row}")
    
    # 3. Shapes (círculos)
    log("\n--- SHAPES (CIRCULOS/FORMAS) ---")
    shape_count = ws.Shapes.Count
    log(f"Total shapes: {shape_count}")
    
    for i in range(1, shape_count + 1):
        try:
            shape = ws.Shapes(i)
            name = shape.Name
            shape_type = shape.Type
            
            # Solo mostrar si parece círculo o oval
            log(f"\n  Shape #{i}: {name}")
            log(f"    Type: {shape_type}")
            log(f"    Position: Top={shape.Top:.1f}, Left={shape.Left:.1f}")
            
            try:
                cell = shape.TopLeftCell
                log(f"    TopLeftCell: {cell.Address}")
            except:
                pass
            
            # Color de relleno
            try:
                rgb = shape.Fill.ForeColor.RGB
                # Convertir RGB de Excel (BGR format)
                b = (rgb >> 16) & 0xFF
                g = (rgb >> 8) & 0xFF
                r = rgb & 0xFF
                log(f"    FillColor RGB: R={r}, G={g}, B={b}")
                log(f"    Fill Visible: {shape.Fill.Visible}")
            except Exception as e:
                log(f"    Fill: Error - {e}")
                
        except Exception as e:
            log(f"  Shape #{i}: Error - {e}")
    
    # 4. Filas de firmas
    log("\n--- CELDAS DE FIRMAS (filas 52-60) ---")
    for row in range(52, 61):
        row_data = []
        for col in range(1, 20):
            val = ws.Cells(row, col).Value
            if val and str(val).strip():
                col_letter = chr(64 + col) if col <= 26 else f"Col{col}"
                row_data.append(f"{col_letter}{row}='{str(val)[:25]}'")
        if row_data:
            log(f"  Fila {row}: {', '.join(row_data)}")
    
    wb.Close(False)
    excel.Quit()
    
    # Guardar
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"\n*** Resultados guardados en: {OUTPUT_FILE} ***")

if __name__ == '__main__':
    analyze_complete()
