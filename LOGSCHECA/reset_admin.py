"""Script para resetear la contraseña del admin."""
import sys
sys.path.insert(0, '.')

from webapp.app import app
from webapp.models import db, User

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if admin:
        admin.set_password('Admin123!')
        admin.failed_login_attempts = 0
        admin.locked_until = None
        admin.is_permanently_locked = False
        admin.must_change_password = False
        db.session.commit()
        print("=" * 50)
        print("✅ Contraseña del admin reseteada")
        print("   Usuario: admin")
        print("   Contraseña: Admin123!")
        print("=" * 50)
    else:
        print("❌ No existe usuario admin")
