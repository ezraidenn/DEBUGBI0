"""Script para ver el HTML renderizado del sidebar"""
import requests
from bs4 import BeautifulSoup

# Hacer login primero
session = requests.Session()
login_url = 'http://localhost:5000/login'
dashboard_url = 'http://localhost:5000/dashboard'

# Login
login_data = {
    'username': 'admin',
    'password': 'admin123'
}

try:
    # Intentar login
    response = session.post(login_url, data=login_data, allow_redirects=False)
    print(f"Login response: {response.status_code}")
    
    # Obtener dashboard
    response = session.get(dashboard_url)
    print(f"Dashboard response: {response.status_code}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Encontrar el sidebar
        sidebar = soup.find('nav', class_='sidebar')
        if sidebar:
            # Encontrar todos los nav-item
            nav_items = sidebar.find_all('li', class_='nav-item')
            
            print("\n" + "="*80)
            print("ELEMENTOS DEL SIDEBAR RENDERIZADOS:")
            print("="*80)
            
            for i, item in enumerate(nav_items, 1):
                # Buscar el enlace
                link = item.find('a', class_='nav-link')
                if link:
                    text = link.find('span')
                    icon = link.find('i')
                    classes = ' '.join(link.get('class', []))
                    
                    print(f"\n{i}. {text.get_text(strip=True) if text else 'N/A'}")
                    print(f"   Clases del enlace: {classes}")
                    print(f"   Icono: {icon.get('class') if icon else 'N/A'}")
                    print(f"   HTML: {str(item)[:200]}...")
                else:
                    # Puede ser un heading
                    heading = item.find('div', class_='sidebar-heading')
                    if heading:
                        print(f"\n{i}. [HEADING] {heading.get_text(strip=True)}")
                    else:
                        print(f"\n{i}. [OTRO] {str(item)[:100]}...")
        else:
            print("No se encontró el sidebar")
    else:
        print(f"Error: No se pudo acceder al dashboard")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
