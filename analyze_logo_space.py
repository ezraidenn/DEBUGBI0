"""
Analizar el espacio real disponible para el logo en el template
"""
import win32com.client
import os

TEMPLATE_PATH = r"webapp\templates\F-RH-18-MIT-FORMATO-DE-MOVIMIENTO-DE-PERSONAL-3(1).xlsx"

def analyze_space():
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    
    try:
        wb = excel.Workbooks.Open(os.path.abspath(TEMPLATE_PATH))
        sheet = wb.ActiveSheet
        
        print("=== ANÁLISIS DEL ESPACIO DISPONIBLE ===\n")
        
        # Logo original
        logo = sheet.Shapes(25)
        print(f"Logo Original (Shape 25):")
        print(f"  Left: {logo.Left}")
        print(f"  Top: {logo.Top}")
        print(f"  Width: {logo.Width}")
        print(f"  Height: {logo.Height}")
        print(f"  Right: {logo.Left + logo.Width}")
        print(f"  Bottom: {logo.Top + logo.Height}")
        
        # Analizar celdas cercanas
        print(f"\n=== CELDAS CERCANAS ===")
        
        # Fila 4 (donde está el logo)
        print(f"\nFila 4 (header):")
        print(f"  Altura: {sheet.Rows(4).RowHeight}")
        
        # Fila 5
        print(f"\nFila 5:")
        print(f"  Altura: {sheet.Rows(5).RowHeight}")
        
        # Columnas A-D (área del logo)
        for col in ['A', 'B', 'C', 'D', 'E']:
            cell = sheet.Range(col + '4')
            print(f"\nColumna {col}:")
            print(f"  Ancho: {sheet.Columns(col).ColumnWidth}")
            print(f"  Left: {cell.Left}")
            print(f"  Width: {cell.Width}")
        
        # Buscar el texto "MOVIMIENTO DE PERSONAL"
        print(f"\n=== LÍMITES DEL ESPACIO ===")
        
        # El logo debe caber entre:
        # - Izquierda: Borde de celda A
        # - Derecha: Antes del texto "MOVIMIENTO DE PERSONAL"
        # - Arriba: Top de fila 4
        # - Abajo: Antes de la fila 8 (donde empieza "Nombre")
        
        cell_a4 = sheet.Range('A4')
        cell_e4 = sheet.Range('E4')
        cell_a8 = sheet.Range('A8')
        
        max_width = cell_e4.Left - cell_a4.Left  # Desde A hasta antes de E
        max_height = cell_a8.Top - cell_a4.Top   # Desde fila 4 hasta fila 8
        
        print(f"\nEspacio máximo disponible:")
        print(f"  Ancho máximo: {max_width} (desde celda A hasta antes de E)")
        print(f"  Alto máximo: {max_height} (desde fila 4 hasta fila 8)")
        print(f"\nComparación con logo actual:")
        print(f"  Logo usa: {logo.Width} de ancho ({(logo.Width/max_width)*100:.1f}%)")
        print(f"  Logo usa: {logo.Height} de alto ({(logo.Height/max_height)*100:.1f}%)")
        
        wb.Close(SaveChanges=False)
        
    finally:
        excel.Quit()

if __name__ == '__main__':
    analyze_space()
