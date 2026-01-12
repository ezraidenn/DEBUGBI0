# 🚀 Configuración de Auto-Deploy desde GitHub

## ✅ Estado Actual

Tu repositorio **YA TIENE** configurado el sistema de auto-deploy con GitHub Actions. El archivo `.github/workflows/deploy.yml` está listo y funcionando.

**Cada vez que hagas `git push` a la rama `main`, se desplegará automáticamente en el servidor.**

---

## 📋 Lo que necesitas hacer AHORA

### 1️⃣ Configurar el Servidor de Producción (10.0.2.64)

Conéctate al servidor Linux y ejecuta el script de setup:

```bash
# Conectarse al servidor
ssh tu_usuario@10.0.2.64

# Clonar el repositorio (solo primera vez)
git clone https://github.com/ezraidenn/DEBUGBI0.git
cd DEBUGBI0

# Ejecutar script de configuración
chmod +x deployment/setup-server.sh
sudo ./deployment/setup-server.sh
```

Este script creará:
- ✅ Usuario `deploy`
- ✅ Estructura de directorios en `/var/www/biostar-monitor/`
- ✅ Servicio systemd
- ✅ Nginx como reverse proxy
- ✅ Configuración de sudoers

---

### 2️⃣ Configurar Variables de Entorno en el Servidor

Edita el archivo `.env` en el servidor:

```bash
sudo nano /var/www/biostar-monitor/shared/.env
```

Copia esta configuración (usa tus valores reales):

```env
# ============================================
# BioStar 2 API Configuration
# ============================================
BIOSTAR_HOST=https://10.0.0.100
BIOSTAR_USER=rcetina
BIOSTAR_PASSWORD=aP1su.ser

# ============================================
# SEGURIDAD - CRÍTICO
# ============================================
SECRET_KEY=586de10a4e4af3e0267040987552b53a3af9f81f4cb20ba4c18d6f36eda16b93
FLASK_ENV=production
TEMPLATES_AUTO_RELOAD=false

# ============================================
# Base de Datos
# ============================================
DATABASE_URL=sqlite:///instance/biostar_users.db

# ============================================
# Cache Configuration
# ============================================
REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=true

# ============================================
# Configuración de Red
# ============================================
PORT=5000
HOST=0.0.0.0
DEBUG=false
```

**Guarda el archivo:** `Ctrl+O`, `Enter`, `Ctrl+X`

---

### 3️⃣ Generar SSH Keys para GitHub Actions

En el servidor, ejecuta:

```bash
# Generar par de claves SSH
ssh-keygen -t ed25519 -C "github-actions-deploy" -f /tmp/biostar_deploy -N ""

# Copiar clave pública al usuario deploy
sudo mkdir -p /home/deploy/.ssh
sudo cp /tmp/biostar_deploy.pub /home/deploy/.ssh/authorized_keys
sudo chown -R deploy:deploy /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
sudo chmod 600 /home/deploy/.ssh/authorized_keys

# Mostrar clave PRIVADA (cópiala completa)
cat /tmp/biostar_deploy
```

**⚠️ IMPORTANTE:** Copia TODA la clave privada (desde `-----BEGIN` hasta `-----END`)

---

### 4️⃣ Configurar GitHub Secrets

Ve a tu repositorio en GitHub:

🔗 **https://github.com/ezraidenn/DEBUGBI0/settings/secrets/actions**

Crea estos 3 secrets:

| Secret Name | Valor | Descripción |
|------------|-------|-------------|
| `SSH_PRIVATE_KEY` | Contenido completo de `/tmp/biostar_deploy` | Clave privada SSH (incluye BEGIN y END) |
| `SERVER_HOST` | `10.0.2.64` | IP del servidor de producción |
| `SERVER_USER` | `deploy` | Usuario para deployment |

**Pasos:**
1. Click en "New repository secret"
2. Name: `SSH_PRIVATE_KEY`
3. Secret: Pega la clave privada completa
4. Click "Add secret"
5. Repite para `SERVER_HOST` y `SERVER_USER`

---

### 5️⃣ Eliminar Clave Privada del Servidor (Seguridad)

Una vez que hayas copiado la clave a GitHub:

```bash
# Eliminar clave privada del servidor
rm /tmp/biostar_deploy
rm /tmp/biostar_deploy.pub

# Verificar que se eliminó
ls /tmp/biostar_deploy*
```

---

## 🎯 Probar el Auto-Deploy

### Opción A: Hacer un cambio y push

```bash
# En tu máquina Windows (en el directorio del proyecto)
cd C:\Users\Administrador\Documents\DebugBi0\DEBUGBI0

# Hacer un cambio pequeño (ejemplo)
echo "# Test auto-deploy" >> README.md

# Commit y push
git add .
git commit -m "test: Probar auto-deploy"
git push origin main
```

### Opción B: Deploy manual desde GitHub

1. Ve a: https://github.com/ezraidenn/DEBUGBI0/actions
2. Click en "Deploy to Production"
3. Click en "Run workflow"
4. Selecciona rama "main"
5. Click en "Run workflow"

---

## 📊 Monitorear el Deploy

### Ver progreso en GitHub
- Ve a: https://github.com/ezraidenn/DEBUGBI0/actions
- Verás el workflow ejecutándose en tiempo real

### Ver logs en el servidor
```bash
# Conectarse al servidor
ssh tu_usuario@10.0.2.64

# Ver logs del servicio
sudo journalctl -u biostar-monitor -f

# Ver estado del servicio
sudo systemctl status biostar-monitor

# Ver releases desplegados
ls -lt /var/www/biostar-monitor/releases/
```

---

## ✅ Verificar que Funciona

Después del deploy (toma ~2-3 minutos):

1. **Abre tu navegador:**
   - URL: `http://10.0.2.64`

2. **Login:**
   - Usuario: `admin`
   - Password: `admin123`

3. **Verifica que la aplicación funciona correctamente**

---

## 🔄 Flujo de Trabajo Normal

Desde ahora, cada vez que quieras desplegar cambios:

```bash
# 1. Hacer cambios en tu código
# 2. Commit
git add .
git commit -m "feat: nueva funcionalidad"

# 3. Push a main (auto-deploy automático)
git push origin main

# 4. Esperar 2-3 minutos
# 5. Verificar en http://10.0.2.64
```

**¡Eso es todo! El deploy es 100% automático.**

---

## 🆘 Comandos Útiles

### En el servidor

```bash
# Ver logs en tiempo real
sudo journalctl -u biostar-monitor -f

# Reiniciar servicio
sudo systemctl restart biostar-monitor

# Ver estado
sudo systemctl status biostar-monitor

# Rollback al release anterior
cd /var/www/biostar-monitor
./deployment/rollback.sh

# Ver releases disponibles
ls -lt /var/www/biostar-monitor/releases/
```

### En tu máquina Windows

```bash
# Ver historial de commits
git log --oneline -10

# Ver estado del repositorio
git status

# Ver branches
git branch -a

# Forzar push (solo si es necesario)
git push origin main --force
```

---

## 🎉 Resumen

### ✅ Lo que YA TIENES:
- ✅ Repositorio en GitHub: https://github.com/ezraidenn/DEBUGBI0
- ✅ GitHub Actions configurado (`.github/workflows/deploy.yml`)
- ✅ Scripts de deployment listos (`deployment/`)
- ✅ Configuración `.env` lista

### 📝 Lo que DEBES HACER:
1. ⬜ Ejecutar `setup-server.sh` en el servidor (10.0.2.64)
2. ⬜ Configurar `.env` en `/var/www/biostar-monitor/shared/.env`
3. ⬜ Generar SSH keys en el servidor
4. ⬜ Configurar GitHub Secrets (SSH_PRIVATE_KEY, SERVER_HOST, SERVER_USER)
5. ⬜ Hacer un push a `main` para probar

### 🚀 Después de eso:
- **Cada push a `main` = Deploy automático**
- **Sin intervención manual**
- **Rollback automático si falla**
- **Mantiene últimas 5 releases**

---

## 📚 Documentación Adicional

- **Guía completa de deployment:** `DEPLOYMENT.md`
- **Guía rápida:** `QUICKSTART.md`
- **Configuración de red:** `CONFIGURACION_RED.md`

---

**Última actualización:** Enero 2026

**¿Necesitas ayuda?** Revisa los logs con `sudo journalctl -u biostar-monitor -f`
