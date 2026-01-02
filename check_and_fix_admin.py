"""Script para verificar y corregir el estado del admin."""
import sys
sys.path.insert(0, '.')

from webapp.app import app
from webapp.models import db, User
from webapp.security import AccountLockout

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print("=" * 60)
        print("📊 ESTADO ACTUAL DEL ADMIN")
        print("=" * 60)
        print(f"Usuario: {admin.username}")
        print(f"Email: {admin.email}")
        print(f"is_active: {admin.is_active}")
        print(f"is_permanently_locked: {admin.is_permanently_locked}")
        print(f"locked_until: {admin.locked_until}")
        print(f"failed_login_attempts: {admin.failed_login_attempts}")
        print(f"must_change_password: {admin.must_change_password}")
        print(f"Bloqueo en memoria: {AccountLockout.is_permanently_locked('admin')}")
        print("=" * 60)
        
        print("\n🔧 APLICANDO CORRECCIONES...")
        
        # Desbloquear completamente en BD
        admin.is_active = True
        admin.is_permanently_locked = False
        admin.locked_until = None
        admin.failed_login_attempts = 0
        admin.must_change_password = False
        admin.last_failed_login = None
        
        # Establecer contraseña
        admin.set_password('admin123', save_history=False)
        
        db.session.commit()
        
        # Limpiar bloqueo en memoria
        AccountLockout.unlock('admin')
        print("✓ Bloqueo en memoria eliminado")
        
        print("\n" + "=" * 60)
        print("✅ ADMIN CORREGIDO EXITOSAMENTE")
        print("=" * 60)
        print(f"Usuario: admin")
        print(f"Contraseña: admin123")
        print(f"Estado: Activo y desbloqueado (BD + Memoria)")
        print("=" * 60)
    else:
        print("❌ No existe usuario admin")
