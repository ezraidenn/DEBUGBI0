# 🚀 QUICKSTART - Configuración Inicial con Auto-Deploy

Guía rápida para configurar el servidor y activar deployments automáticos desde GitHub.

---

## 📋 Requisitos

- **Servidor Linux**: Ubuntu 20.04+ o Debian 11+
- **Python**: 3.11+
- **RAM**: Mínimo 2GB
- **Acceso SSH** al servidor
- **Cuenta GitHub** con acceso al repositorio

---

## ⚡ Instalación Rápida (5 minutos)

### 1️⃣ En el Servidor Linux

```bash
# Conectarse al servidor
ssh tu_usuario@10.0.2.64

# Clonar el repositorio
git clone https://github.com/ezraidenn/DEBUGBI0.git
cd DEBUGBI0

# Ejecutar script de configuración automática
chmod +x deployment/setup-server.sh
sudo ./deployment/setup-server.sh
```

**El script automáticamente:**
- ✅ Crea usuario `deploy`
- ✅ Crea estructura de directorios en `/var/www/biostar-monitor/`
- ✅ Instala Python, Nginx, y dependencias
- ✅ Configura servicio systemd
- ✅ Configura Nginx como reverse proxy
- ✅ Prepara todo para recibir deployments

---

### 2️⃣ Configurar Variables de Entorno

```bash
# Editar archivo de configuración
sudo nano /var/www/biostar-monitor/shared/.env
```

**Contenido del .env:**
```env
# BioStar Configuration
BIOSTAR_URL=https://10.0.0.100
BIOSTAR_USERNAME=admin
BIOSTAR_PASSWORD=TU_PASSWORD_AQUI

# Flask Configuration
FLASK_SECRET_KEY=GENERA_UNA_CLAVE_ALEATORIA_AQUI
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

---

### 3️⃣ Configurar SSH para GitHub Actions

**En tu máquina local (Windows/Mac/Linux):**

```bash
# Generar par de claves SSH
ssh-keygen -t ed25519 -C "github-deploy" -f biostar_deploy

# Esto crea 2 archivos:
# - biostar_deploy (privada) → Para GitHub Secret
# - biostar_deploy.pub (pública) → Para el servidor
```

**Copiar clave pública al servidor:**

```bash
# Opción 1: Usando ssh-copy-id (Linux/Mac)
ssh-copy-id -i biostar_deploy.pub deploy@10.0.2.64

# Opción 2: Manual
cat biostar_deploy.pub
# Copiar el contenido y pegarlo en el servidor:
```

**En el servidor:**
```bash
# Cambiar a usuario deploy
sudo su - deploy

# Crear directorio SSH si no existe
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Agregar clave pública
nano ~/.ssh/authorized_keys
# Pegar la clave pública aquí

# Ajustar permisos
chmod 600 ~/.ssh/authorized_keys
exit
```

---

### 4️⃣ Configurar GitHub Secrets

Ve a: **https://github.com/ezraidenn/DEBUGBI0/settings/secrets/actions**

Click en **"New repository secret"** y agrega estos 3 secrets:

| Secret Name | Valor | Dónde obtenerlo |
|------------|-------|-----------------|
| `SSH_PRIVATE_KEY` | Contenido completo de `biostar_deploy` | `cat biostar_deploy` |
| `SERVER_HOST` | `10.0.2.64` | IP de tu servidor |
| `SERVER_USER` | `deploy` | Usuario de deployment |

**Para SSH_PRIVATE_KEY:**
```bash
# En tu máquina local
cat biostar_deploy

# Copiar TODO el contenido (incluyendo -----BEGIN y -----END)
# Pegarlo en el secret de GitHub
```

---

### 5️⃣ Primer Deployment Manual

**Opción A: Desde GitHub UI**
1. Ve a: https://github.com/ezraidenn/DEBUGBI0/actions
2. Click en **"Deploy to Production"**
3. Click en **"Run workflow"**
4. Selecciona rama **"main"**
5. Click **"Run workflow"**

**Opción B: Hacer push a main**
```bash
# En tu máquina local
git add .
git commit -m "Initial deployment"
git push origin main
```

---

### 6️⃣ Verificar Deployment

**En el servidor:**
```bash
# Ver estado del servicio
sudo systemctl status biostar-monitor

# Ver logs en tiempo real
sudo journalctl -u biostar-monitor -f

# Ver release activo
ls -la /var/www/biostar-monitor/current

# Verificar que Nginx está corriendo
sudo systemctl status nginx
```

**Acceder a la aplicación:**
```
http://10.0.2.64
```

**Credenciales por defecto:**
- Usuario: `admin`
- Contraseña: `admin123`

---

## 🔄 Deployments Automáticos

### ¡Ya está todo configurado!

Cada vez que hagas **push a la rama `main`**, GitHub Actions automáticamente:

1. ✅ Ejecuta tests
2. ✅ Construye el artefacto
3. ✅ Lo sube al servidor
4. ✅ Crea nuevo release en `/var/www/biostar-monitor/releases/TIMESTAMP/`
5. ✅ Cambia el symlink `current` al nuevo release (atómico)
6. ✅ Reinicia el servicio
7. ✅ Limpia releases antiguos (mantiene últimas 5)

**Workflow típico:**
```bash
# Hacer cambios en el código
git add .
git commit -m "feat: nueva funcionalidad"
git push origin main

# ¡Listo! En ~2 minutos estará en producción
```

---

## ⏮️ Rollback Rápido

Si algo sale mal después de un deployment:

```bash
# En el servidor
cd /var/www/biostar-monitor

# Rollback al release anterior
./deployment/rollback.sh

# O a un release específico
ls -t releases/
./deployment/rollback.sh 20260112_140815
```

---

## 📊 Monitoreo

### Ver logs del servicio
```bash
# Logs en tiempo real
sudo journalctl -u biostar-monitor -f

# Últimas 100 líneas
sudo journalctl -u biostar-monitor -n 100

# Solo errores
sudo journalctl -u biostar-monitor -p err
```

### Ver logs de la aplicación
```bash
tail -f /var/www/biostar-monitor/shared/logs/app.log
```

### Estado del servicio
```bash
# Ver estado
sudo systemctl status biostar-monitor

# Reiniciar manualmente
sudo systemctl restart biostar-monitor

# Ver releases disponibles
ls -lt /var/www/biostar-monitor/releases/
```

---

## 🔧 Troubleshooting

### El servicio no inicia

```bash
# Ver logs detallados
sudo journalctl -u biostar-monitor -n 100 --no-pager

# Verificar permisos
sudo chown -R deploy:deploy /var/www/biostar-monitor

# Probar manualmente
cd /var/www/biostar-monitor/current
source venv/bin/activate
python run_production.py
```

### GitHub Actions falla

1. Revisa los logs en: https://github.com/ezraidenn/DEBUGBI0/actions
2. Verifica que los secrets estén configurados
3. Prueba SSH manualmente:
   ```bash
   ssh deploy@10.0.2.64 "ls -la /var/www/biostar-monitor"
   ```

### No puedo acceder a la aplicación

```bash
# Verificar que Nginx está corriendo
sudo systemctl status nginx

# Verificar que el servicio está corriendo
sudo systemctl status biostar-monitor

# Ver puerto 5000
sudo netstat -tulpn | grep :5000

# Reiniciar Nginx
sudo systemctl restart nginx
```

---

## 📁 Estructura Final en el Servidor

```
/var/www/biostar-monitor/
├── releases/
│   ├── 20260112_140815/  ← Release actual
│   │   ├── webapp/
│   │   ├── src/
│   │   ├── venv/
│   │   └── run_production.py
│   ├── 20260112_131233/  ← Release anterior
│   └── 20260112_120501/
├── current → releases/20260112_140815/  ← Symlink
└── shared/
    ├── .env              ← Configuración
    ├── instance/         ← Base de datos
    │   └── biostar_users.db
    ├── logs/            ← Logs
    └── uploads/         ← Archivos subidos
```

---

## ✅ Checklist de Configuración

- [ ] Script `setup-server.sh` ejecutado
- [ ] Archivo `.env` configurado con credenciales reales
- [ ] Par de claves SSH generado
- [ ] Clave pública agregada a `/home/deploy/.ssh/authorized_keys`
- [ ] GitHub Secrets configurados (SSH_PRIVATE_KEY, SERVER_HOST, SERVER_USER)
- [ ] Primer deployment ejecutado exitosamente
- [ ] Servicio corriendo: `sudo systemctl status biostar-monitor`
- [ ] Nginx corriendo: `sudo systemctl status nginx`
- [ ] Aplicación accesible en `http://10.0.2.64`
- [ ] Login funcional con credenciales por defecto

---

## 🎉 ¡Listo!

Tu servidor ahora:
- ✅ Recibe deployments automáticos en cada push a `main`
- ✅ Mantiene historial de releases para rollback
- ✅ Se reinicia automáticamente en caso de fallo
- ✅ Tiene logs centralizados
- ✅ Está protegido con Nginx como reverse proxy

**Próximos pasos:**
1. Cambiar contraseña de admin
2. Configurar dominio (opcional)
3. Configurar SSL/HTTPS con Let's Encrypt (recomendado)
4. Configurar backups automáticos de la base de datos

---

## 📚 Documentación Adicional

- **Deployment completo**: Ver `DEPLOYMENT.md`
- **Configuración avanzada**: Ver `README.md`
- **Troubleshooting**: Ver sección correspondiente en `DEPLOYMENT.md`

---

**¿Problemas?** Revisa los logs:
```bash
sudo journalctl -u biostar-monitor -n 100
```

**Última actualización**: Enero 2026
