"""
Test para verificar el escalado de logos
"""
import win32com.client
import os

TEMPLATE_PATH = r"webapp\templates\F-RH-18-MIT-FORMATO-DE-MOVIMIENTO-DE-PERSONAL-3(1).xlsx"
LOGO_DRELEX = r"webapp\static\logos\DRELEX.png"
LOGO_EKOGOLF = r"webapp\static\logos\Ekogolf.jpeg"

def test_logo_scaling():
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = True  # Visible para ver el resultado
    excel.DisplayAlerts = False
    
    try:
        # Abrir template
        wb = excel.Workbooks.Open(os.path.abspath(TEMPLATE_PATH))
        sheet = wb.ActiveSheet
        
        # Obtener propiedades del logo original
        original_logo = sheet.Shapes(25)
        original_left = original_logo.Left
        original_top = original_logo.Top
        original_width = original_logo.Width
        original_height = original_logo.Height
        
        print(f"=== LOGO ORIGINAL (MIT) ===")
        print(f"Left: {original_left}")
        print(f"Top: {original_top}")
        print(f"Width: {original_width}")
        print(f"Height: {original_height}")
        
        # Eliminar logo original
        original_logo.Delete()
        
        # Insertar DRELEX
        logo_path = os.path.abspath(LOGO_DRELEX)
        print(f"\n=== INSERTANDO DRELEX ===")
        print(f"Path: {logo_path}")
        
        picture = sheet.Shapes.AddPicture(
            Filename=logo_path,
            LinkToFile=False,
            SaveWithDocument=True,
            Left=original_left,
            Top=original_top,
            Width=-1,
            Height=-1
        )
        
        # Dimensiones originales del archivo
        current_width = picture.Width
        current_height = picture.Height
        print(f"Dimensiones originales del archivo: {current_width} x {current_height}")
        
        # Bloquear aspect ratio
        picture.LockAspectRatio = -1
        
        # Calcular factores de escala
        scale_width = original_width / current_width
        scale_height = original_height / current_height
        
        print(f"\nFactores de escala:")
        print(f"  scale_width = {original_width} / {current_width} = {scale_width:.4f}")
        print(f"  scale_height = {original_height} / {current_height} = {scale_height:.4f}")
        print(f"  max(scale_width, scale_height) = {max(scale_width, scale_height):.4f}")
        
        # Usar el factor MAYOR
        scale_factor = max(scale_width, scale_height)
        
        print(f"\nAplicando escala con factor: {scale_factor:.4f}")
        picture.Width = current_width * scale_factor
        
        print(f"\nDimensiones finales:")
        print(f"  Width: {picture.Width}")
        print(f"  Height: {picture.Height}")
        
        # Verificar límites
        if picture.Width > original_width:
            print(f"  ⚠ Width excede límite, ajustando de {picture.Width} a {original_width}")
            picture.Width = original_width
        if picture.Height > original_height:
            print(f"  ⚠ Height excede límite, ajustando de {picture.Height} a {original_height}")
            picture.Height = original_height
        
        print(f"\nDimensiones después de verificar límites:")
        print(f"  Width: {picture.Width}")
        print(f"  Height: {picture.Height}")
        
        # Quitar bordes
        picture.Line.Visible = 0
        picture.Shadow.Visible = 0
        
        print("\n✓ Logo DRELEX insertado. Revisa Excel visualmente.")
        input("Presiona Enter para cerrar...")
        
        wb.Close(SaveChanges=False)
        
    finally:
        excel.Quit()

if __name__ == '__main__':
    test_logo_scaling()
