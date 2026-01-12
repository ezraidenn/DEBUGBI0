# 🚀 Deployment Guide - BioStar Logs Monitor

Guía completa de deployment profesional con CI/CD automático usando GitHub Actions y systemd.

## 📋 Tabla de Contenidos

- [Arquitectura de Deployment](#arquitectura-de-deployment)
- [Configuración Inicial del Servidor](#configuración-inicial-del-servidor)
- [Configuración de GitHub](#configuración-de-github)
- [Proceso de Deployment](#proceso-de-deployment)
- [Rollback](#rollback)
- [Monitoreo y Logs](#monitoreo-y-logs)
- [Troubleshooting](#troubleshooting)

---

## 🏗️ Arquitectura de Deployment

### Estructura en el Servidor

```
/var/www/biostar-monitor/
├── releases/
│   ├── 20260112_120501/      # Release antiguo
│   ├── 20260112_131233/      # Release anterior
│   └── 20260112_140815/      # Release actual
├── current -> releases/20260112_140815/  # Symlink al release activo
└── shared/
    ├── .env                   # Configuración de producción
    ├── instance/              # Base de datos SQLite
    │   └── biostar_users.db
    ├── logs/                  # Logs de la aplicación
    └── uploads/               # Archivos subidos (si aplica)
```

### Flujo de Deployment

```
┌─────────────┐
│ Git Push    │
│ to main     │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ GitHub Actions      │
│ - Checkout          │
│ - Tests             │
│ - Build artifact    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Upload to Server    │
│ via SSH/SCP         │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Server              │
│ - Extract release   │
│ - Install deps      │
│ - Symlink shared    │
│ - Switch 'current'  │
│ - Restart service   │
└─────────────────────┘
```

---

## ⚙️ Configuración Inicial del Servidor

### 1. Requisitos del Servidor

- **OS**: Ubuntu 20.04+ / Debian 11+
- **Python**: 3.11+
- **RAM**: Mínimo 2GB
- **Disco**: Mínimo 10GB libres
- **Red**: Acceso a BioStar 2 (10.0.0.100)

### 2. Ejecutar Script de Setup

En el servidor de producción:

```bash
# Clonar el repositorio (solo para setup inicial)
git clone https://github.com/TU_USUARIO/biostar-monitor.git
cd biostar-monitor

# Ejecutar script de configuración
chmod +x deployment/setup-server.sh
sudo ./deployment/setup-server.sh
```

Este script:
- ✅ Crea usuario `deploy`
- ✅ Crea estructura de directorios
- ✅ Instala dependencias del sistema
- ✅ Configura systemd service
- ✅ Configura Nginx como reverse proxy
- ✅ Configura sudoers para restart sin password

### 3. Configurar Variables de Entorno

Edita `/var/www/biostar-monitor/shared/.env`:

```bash
sudo nano /var/www/biostar-monitor/shared/.env
```

```env
# BioStar Configuration
BIOSTAR_URL=https://10.0.0.100
BIOSTAR_USERNAME=admin
BIOSTAR_PASSWORD=TU_PASSWORD_REAL

# Flask Configuration
FLASK_SECRET_KEY=genera-una-clave-aleatoria-segura-aqui
FLASK_ENV=production
DEBUG=False

# Database
DATABASE_URL=sqlite:///instance/biostar_users.db

# Security
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Server
HOST=0.0.0.0
PORT=5000
```

**Generar SECRET_KEY segura:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Configurar SSH para GitHub Actions

```bash
# Generar par de claves SSH (en tu máquina local)
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/biostar_deploy

# Copiar clave pública al servidor
ssh-copy-id -i ~/.ssh/biostar_deploy.pub deploy@TU_SERVIDOR

# Guardar clave privada para GitHub Secrets
cat ~/.ssh/biostar_deploy
```

---

## 🔐 Configuración de GitHub

### 1. Crear Repositorio

```bash
# En tu máquina local, en el directorio del proyecto
git init
git add .
git commit -m "Initial commit - BioStar Monitor"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/biostar-monitor.git
git push -u origin main
```

### 2. Configurar Secrets

Ve a: **Settings → Secrets and variables → Actions → New repository secret**

Agrega los siguientes secrets:

| Secret Name | Valor | Descripción |
|------------|-------|-------------|
| `SSH_PRIVATE_KEY` | Contenido de `~/.ssh/biostar_deploy` | Clave privada SSH |
| `SERVER_HOST` | `10.0.2.64` o tu IP/dominio | IP del servidor |
| `SERVER_USER` | `deploy` | Usuario de deployment |

---

## 🚀 Proceso de Deployment

### Deployment Automático

Cada vez que hagas `push` a la rama `main`:

```bash
git add .
git commit -m "feat: nueva funcionalidad"
git push origin main
```

GitHub Actions automáticamente:
1. ✅ Ejecuta tests
2. ✅ Construye el artefacto
3. ✅ Lo sube al servidor
4. ✅ Despliega atómicamente
5. ✅ Reinicia el servicio

### Deployment Manual

Desde GitHub:
1. Ve a **Actions**
2. Selecciona **Deploy to Production**
3. Click en **Run workflow**
4. Selecciona rama `main`
5. Click **Run workflow**

### Verificar Deployment

```bash
# En el servidor
sudo systemctl status biostar-monitor

# Ver logs en tiempo real
sudo journalctl -u biostar-monitor -f

# Ver release activo
ls -la /var/www/biostar-monitor/current

# Ver releases disponibles
ls -lt /var/www/biostar-monitor/releases/
```

---

## ⏮️ Rollback

### Rollback Automático al Release Anterior

```bash
# En el servidor
cd /var/www/biostar-monitor
./deployment/rollback.sh
```

### Rollback a Release Específico

```bash
# Listar releases disponibles
ls -t /var/www/biostar-monitor/releases/

# Rollback a release específico
./deployment/rollback.sh 20260112_120501
```

### Rollback Manual

```bash
# Ver releases disponibles
ls -lt /var/www/biostar-monitor/releases/

# Cambiar symlink manualmente
sudo ln -sfn /var/www/biostar-monitor/releases/20260112_120501 /var/www/biostar-monitor/current

# Reiniciar servicio
sudo systemctl restart biostar-monitor
```

---

## 📊 Monitoreo y Logs

### Ver Logs del Servicio

```bash
# Logs en tiempo real
sudo journalctl -u biostar-monitor -f

# Últimas 100 líneas
sudo journalctl -u biostar-monitor -n 100

# Logs de hoy
sudo journalctl -u biostar-monitor --since today

# Logs con errores
sudo journalctl -u biostar-monitor -p err
```

### Ver Logs de la Aplicación

```bash
# Logs de Flask
tail -f /var/www/biostar-monitor/shared/logs/app.log

# Logs de seguridad
tail -f /var/www/biostar-monitor/shared/logs/security_audit.log
```

### Estado del Servicio

```bash
# Estado actual
sudo systemctl status biostar-monitor

# Reiniciar
sudo systemctl restart biostar-monitor

# Detener
sudo systemctl stop biostar-monitor

# Iniciar
sudo systemctl start biostar-monitor

# Ver si está habilitado en boot
sudo systemctl is-enabled biostar-monitor
```

### Monitoreo de Recursos

```bash
# CPU y memoria del proceso
ps aux | grep biostar-monitor

# Uso de disco
df -h /var/www/biostar-monitor

# Tamaño de releases
du -sh /var/www/biostar-monitor/releases/*

# Conexiones activas
sudo netstat -tulpn | grep :5000
```

---

## 🔧 Troubleshooting

### El servicio no inicia

```bash
# Ver logs detallados
sudo journalctl -u biostar-monitor -n 100 --no-pager

# Verificar permisos
ls -la /var/www/biostar-monitor/current
sudo chown -R deploy:deploy /var/www/biostar-monitor

# Verificar .env
cat /var/www/biostar-monitor/shared/.env

# Probar manualmente
cd /var/www/biostar-monitor/current
source venv/bin/activate
python run_production.py
```

### Error de conexión a BioStar

```bash
# Verificar conectividad
ping 10.0.0.100
curl -k https://10.0.0.100

# Verificar credenciales en .env
cat /var/www/biostar-monitor/shared/.env | grep BIOSTAR
```

### Deployment falla en GitHub Actions

1. Revisa los logs en GitHub Actions
2. Verifica que los secrets estén configurados correctamente
3. Prueba SSH manualmente:
   ```bash
   ssh deploy@TU_SERVIDOR "ls -la /var/www/biostar-monitor"
   ```

### Base de datos corrupta

```bash
# Backup de la DB actual
cp /var/www/biostar-monitor/shared/instance/biostar_users.db \
   /var/www/biostar-monitor/shared/instance/biostar_users.db.backup

# Restaurar desde backup
cp /var/www/biostar-monitor/shared/instance/biostar_users.db.backup \
   /var/www/biostar-monitor/shared/instance/biostar_users.db

# Reiniciar servicio
sudo systemctl restart biostar-monitor
```

### Limpiar releases antiguos manualmente

```bash
# Mantener solo últimas 3 releases
cd /var/www/biostar-monitor/releases
ls -t | tail -n +4 | xargs rm -rf
```

---

## 🎯 Mejores Prácticas

### 1. **Siempre prueba localmente antes de push**
```bash
python -m pytest tests/
python run_production.py
```

### 2. **Usa commits descriptivos**
```bash
git commit -m "feat: agregar autenticación de dos factores"
git commit -m "fix: corregir error en cálculo de estadísticas"
git commit -m "docs: actualizar guía de deployment"
```

### 3. **Monitorea después de cada deploy**
```bash
# Inmediatamente después del deploy
sudo journalctl -u biostar-monitor -f
```

### 4. **Backups regulares**
```bash
# Crear script de backup diario
sudo crontab -e

# Agregar:
0 2 * * * /var/www/biostar-monitor/deployment/backup.sh
```

### 5. **Mantén releases limpios**
- GitHub Actions limpia automáticamente (mantiene últimas 5)
- Verifica periódicamente: `du -sh /var/www/biostar-monitor/releases/*`

---

## 📚 Referencias

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [systemd Service Management](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Nginx Reverse Proxy](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [Flask Deployment](https://flask.palletsprojects.com/en/3.0.x/deploying/)

---

## 🆘 Soporte

Si encuentras problemas:
1. Revisa los logs: `sudo journalctl -u biostar-monitor -n 100`
2. Verifica la configuración: `cat /var/www/biostar-monitor/shared/.env`
3. Prueba rollback: `./deployment/rollback.sh`
4. Contacta al equipo de desarrollo

---

**Última actualización**: Enero 2026
