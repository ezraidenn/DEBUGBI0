"""Script para inspeccionar el HTML del sidebar"""
from webapp.app import app
from flask import render_template_string

with app.app_context():
    # Simular un usuario admin autenticado
    from webapp.models import User
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print("Usuario admin encontrado")
        print(f"is_admin: {admin.is_admin}")
        print(f"can_manage_devices: {admin.can_manage_devices}")
        
        # Leer el template base
        with open('webapp/templates/base.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Extraer solo la sección del sidebar
        start = template_content.find('<ul class="nav flex-column"')
        end = template_content.find('</ul>', start) + 5
        sidebar_section = template_content[start:end]
        
        print("\n" + "="*80)
        print("SECCIÓN DEL SIDEBAR EN EL TEMPLATE:")
        print("="*80)
        print(sidebar_section)
