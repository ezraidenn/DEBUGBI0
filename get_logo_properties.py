"""
Script para obtener las propiedades exactas del logo en el template Excel
"""
import win32com.client
import os

TEMPLATE_PATH = r"webapp\templates\F-RH-18-MIT-FORMATO-DE-MOVIMIENTO-DE-PERSONAL-3(1).xlsx"

def get_logo_properties():
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    
    try:
        wb = excel.Workbooks.Open(os.path.abspath(TEMPLATE_PATH))
        sheet = wb.ActiveSheet
        
        # Buscar el logo (Picture)
        print("=== SHAPES EN EL TEMPLATE ===")
        for i in range(1, sheet.Shapes.Count + 1):
            shape = sheet.Shapes(i)
            print(f"\nShape {i}: {shape.Name}")
            print(f"  Type: {shape.Type}")
            
            if shape.Type == 13:  # msoLinkedPicture o msoPicture
                print(f"  ✓ ES UNA IMAGEN")
                print(f"  Left: {shape.Left}")
                print(f"  Top: {shape.Top}")
                print(f"  Width: {shape.Width}")
                print(f"  Height: {shape.Height}")
                print(f"  LockAspectRatio: {shape.LockAspectRatio}")
                
                # Propiedades de formato
                try:
                    print(f"  Line.Visible: {shape.Line.Visible}")
                    print(f"  Shadow.Visible: {shape.Shadow.Visible}")
                except:
                    pass
        
        wb.Close(SaveChanges=False)
        
    finally:
        excel.Quit()

if __name__ == '__main__':
    get_logo_properties()
