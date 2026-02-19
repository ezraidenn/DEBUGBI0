"""
Migración: Agregar tabla companies y company_id a mobper_presets
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from webapp.app import app
from webapp.models import db, Company

def migrate():
    """Ejecuta la migración"""
    with app.app_context():
        print("[MIGRATION] Creando tabla companies...")
        
        # Crear tabla companies si no existe
        db.create_all()
        
        # Agregar columna company_id a mobper_presets si no existe
        try:
            with db.engine.connect() as conn:
                # Verificar si la columna ya existe
                result = conn.execute(db.text("PRAGMA table_info(mobper_presets)"))
                columns = [row[1] for row in result]
                
                if 'company_id' not in columns:
                    print("[MIGRATION] Agregando columna company_id a mobper_presets...")
                    conn.execute(db.text("ALTER TABLE mobper_presets ADD COLUMN company_id INTEGER"))
                    conn.commit()
                    print("[MIGRATION] ✓ Columna company_id agregada")
                else:
                    print("[MIGRATION] ✓ Columna company_id ya existe")
        except Exception as e:
            print(f"[MIGRATION] Error agregando columna: {e}")
        
        # Crear empresas por defecto
        print("[MIGRATION] Creando empresas por defecto...")
        
        empresas_default = [
            {'name': 'MIT', 'logo_filename': None, 'is_active': True},
            {'name': 'Ekogolf', 'logo_filename': 'Ekogolf.jpeg', 'is_active': True},
            {'name': 'DRELEX', 'logo_filename': 'DRELEX.png', 'is_active': True},
        ]
        
        for emp_data in empresas_default:
            existing = Company.query.filter_by(name=emp_data['name']).first()
            if not existing:
                company = Company(**emp_data)
                db.session.add(company)
                print(f"[MIGRATION] ✓ Empresa creada: {emp_data['name']}")
            else:
                print(f"[MIGRATION] - Empresa ya existe: {emp_data['name']}")
        
        db.session.commit()
        print("[MIGRATION] ✓ Migración completada exitosamente")

if __name__ == '__main__':
    migrate()
