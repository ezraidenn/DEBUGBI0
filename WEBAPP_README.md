# 🌐 BioStar Debug Monitor - Aplicación Web

Sistema web completo para monitoreo y debugging de checadores BioStar 2.

## 🎯 Características

### ✅ Autenticación Segura
- Sistema de login con Flask-Login
- Contraseñas hasheadas con Werkzeug
- Sesiones seguras
- Opción "Recordarme"

### 👥 Gestión de Usuarios (Admin)
- Crear, editar y eliminar usuarios
- Asignar roles (Admin/Usuario)
- Activar/desactivar cuentas
- Ver último acceso

### 📊 Dashboard Principal
- Vista general de todos los checadores
- Estadísticas en tiempo real
- Tarjetas por dispositivo con resumen
- Acceso rápido a debug individual

### 🔍 Debug General
- Tabla con todos los checadores
- Resumen de eventos del día
- Exportación masiva a Excel
- Filtros y ordenamiento

### 🐛 Debug Individual por Checador
- Vista detallada de un dispositivo
- Tabla de eventos del día
- Estadísticas específicas
- Exportación a Excel

---

## 🚀 Instalación

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar credenciales
Editar `.env` con las credenciales de BioStar:
```env
BIOSTAR_HOST=https://10.0.0.100
BIOSTAR_USER=rcetina
BIOSTAR_PASSWORD=aP1su.ser
```

### 3. Iniciar la aplicación
```bash
python run_webapp.py
```

La aplicación estará disponible en: **http://localhost:5000**

---

## 🔐 Credenciales por Defecto

**Usuario:** `admin`  
**Contraseña:** `admin123`

⚠️ **IMPORTANTE:** Cambiar la contraseña después del primer inicio de sesión.

---

## 📱 Estructura de la Aplicación

```
webapp/
├── app.py                  # Aplicación Flask principal
├── models.py               # Modelos de base de datos
├── templates/              # Templates HTML
│   ├── base.html          # Layout base
│   ├── login.html         # Página de login
│   ├── dashboard.html     # Dashboard principal
│   ├── debug_general.html # Debug general
│   ├── debug_device.html  # Debug individual
│   ├── users.html         # Lista de usuarios
│   └── user_form.html     # Formulario de usuario
└── biostar_users.db       # Base de datos SQLite (se crea automáticamente)
```

---

## 🎨 Capturas de Pantalla

### Login
- Diseño moderno con gradiente
- Formulario seguro
- Opción "Recordarme"

### Dashboard
- Vista de tarjetas por checador
- Estadísticas generales
- Acceso rápido a funciones

### Debug General
- Tabla completa de todos los checadores
- Resumen de eventos
- Exportación masiva

### Debug Individual
- Eventos detallados por checador
- Gráficas de estadísticas
- Exportación individual

### Gestión de Usuarios (Admin)
- CRUD completo de usuarios
- Asignación de roles
- Control de acceso

---

## 🔒 Seguridad

### Autenticación
- Contraseñas hasheadas con Werkzeug (PBKDF2)
- Sesiones seguras con Flask-Login
- Protección CSRF integrada
- Cookies seguras

### Autorización
- Decorador `@login_required` en todas las rutas
- Verificación de rol admin para gestión de usuarios
- Usuarios pueden ser desactivados

### Base de Datos
- SQLite para simplicidad
- SQLAlchemy ORM para prevenir SQL injection
- Migraciones automáticas

---

## 📋 Rutas Disponibles

### Públicas
- `GET /` - Redirige a login o dashboard
- `GET /login` - Página de login
- `POST /login` - Procesar login
- `GET /logout` - Cerrar sesión

### Protegidas (Requieren Login)
- `GET /dashboard` - Dashboard principal
- `GET /debug/general` - Debug general
- `GET /debug/device/<id>` - Debug individual
- `GET /debug/device/<id>/export` - Exportar debug

### Admin (Requieren Rol Admin)
- `GET /users` - Lista de usuarios
- `GET /users/create` - Crear usuario
- `POST /users/create` - Guardar usuario
- `GET /users/<id>/edit` - Editar usuario
- `POST /users/<id>/edit` - Actualizar usuario
- `POST /users/<id>/delete` - Eliminar usuario

### API
- `GET /api/devices` - Lista de dispositivos (JSON)
- `GET /api/device/<id>/summary` - Resumen de dispositivo (JSON)

---

## 🛠️ Tecnologías Utilizadas

### Backend
- **Flask 3.0.0** - Framework web
- **Flask-Login 0.6.3** - Gestión de sesiones
- **Flask-SQLAlchemy 3.1.1** - ORM
- **Werkzeug 3.0.1** - Utilidades y seguridad
- **Flask-Bcrypt 1.0.1** - Hashing de contraseñas

### Frontend
- **Bootstrap 5.3** - Framework CSS
- **Bootstrap Icons** - Iconos
- **JavaScript Vanilla** - Interactividad

### Base de Datos
- **SQLite** - Base de datos embebida

---

## 📊 Modelos de Datos

### User
```python
- id: Integer (PK)
- username: String (unique)
- email: String (unique)
- password_hash: String
- full_name: String
- is_admin: Boolean
- is_active: Boolean
- created_at: DateTime
- last_login: DateTime
```

---

## 🔧 Configuración Avanzada

### Cambiar Puerto
Editar `run_webapp.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8080)
```

### Cambiar Secret Key
Editar `webapp/app.py`:
```python
app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui'
```

O usar variable de entorno:
```bash
export SECRET_KEY='tu-clave-secreta-aqui'
```

### Usar PostgreSQL/MySQL
Editar `webapp/app.py`:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/dbname'
```

---

## 🐛 Debugging

### Modo Debug
El modo debug está activado por defecto en desarrollo:
```python
app.run(debug=True)
```

### Ver Logs
Los logs se muestran en la consola:
```bash
python run_webapp.py
```

### Errores Comunes

**Error: "No module named 'flask'"**
- Solución: `pip install -r requirements.txt`

**Error: "Error al conectar con BioStar"**
- Verificar credenciales en `.env`
- Verificar conectividad con el servidor

**Error: "Database is locked"**
- Cerrar otras instancias de la aplicación
- Eliminar `biostar_users.db` y reiniciar

---

## 📈 Mejoras Futuras

- [ ] Gráficas interactivas con Chart.js
- [ ] Exportación a PDF
- [ ] Notificaciones en tiempo real
- [ ] Historial de eventos
- [ ] Reportes programados
- [ ] API REST completa
- [ ] Autenticación con LDAP/AD
- [ ] Multi-tenancy

---

## 🆘 Soporte

### Problemas Comunes

1. **No puedo iniciar sesión**
   - Verificar usuario y contraseña
   - Usar credenciales por defecto: admin/admin123

2. **No veo los checadores**
   - Verificar conexión a BioStar
   - Revisar credenciales en `.env`

3. **Error al exportar**
   - Verificar permisos en carpeta `data/outputs/`
   - Verificar que hay eventos del día

---

## 📝 Notas

- La base de datos se crea automáticamente al primer inicio
- El usuario admin se crea automáticamente
- Los archivos Excel se guardan en `data/outputs/`
- La aplicación se conecta a BioStar en cada petición

---

## 🔐 Seguridad en Producción

Para usar en producción:

1. Cambiar `SECRET_KEY`
2. Desactivar modo debug
3. Usar HTTPS
4. Cambiar contraseña de admin
5. Usar base de datos robusta (PostgreSQL)
6. Configurar firewall
7. Usar servidor WSGI (Gunicorn)

---

**¡Disfruta monitoreando tus checadores BioStar!** 🎉
