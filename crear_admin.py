"""Script para crear el usuario admin inicial."""
import sys
sys.path.insert(0, '.')

from webapp.app import app
from webapp.models import db, User

with app.app_context():
    # Verificar si ya existe
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print("=" * 50)
        print("[!] El usuario admin ya existe")
        print("    Usa reset_admin.py para resetear la contraseña")
        print("=" * 50)
    else:
        # Crear nuevo usuario admin
        admin = User(
            username='admin',
            email='admin@biostar.local',
            full_name='Administrador',
            is_admin=True,
            is_active=True,
            can_see_all_events=True,
            can_manage_devices=True,
            must_change_password=False
        )
        
        # Contraseña segura por defecto: Admin123!
        admin.set_password('Admin123!')
        
        db.session.add(admin)
        db.session.commit()
        
        print("=" * 50)
        print("[OK] Usuario admin creado exitosamente")
        print("    Usuario: admin")
        print("    Contraseña: Admin123!")
        print("")
        print("    IMPORTANTE: Cambia esta contraseña")
        print("    después del primer inicio de sesión")
        print("=" * 50)
