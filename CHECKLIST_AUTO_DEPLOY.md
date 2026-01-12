# ✅ Checklist: Configurar Auto-Deploy

## 📊 Estado Actual

### ✅ Ya Configurado (No requiere acción)
- ✅ Repositorio GitHub: https://github.com/ezraidenn/DEBUGBI0
- ✅ GitHub Actions workflow (`.github/workflows/deploy.yml`)
- ✅ Scripts de deployment (`deployment/setup-server.sh`, `deployment/rollback.sh`)
- ✅ Configuración `.env` lista
- ✅ Estructura de proyecto correcta

---

## 📝 Tareas Pendientes

### 1️⃣ Configurar Servidor Linux (10.0.2.64)

**Ubicación:** Servidor de producción (10.0.2.64)

```bash
# ⬜ 1.1 Conectarse al servidor
ssh tu_usuario@10.0.2.64

# ⬜ 1.2 Clonar repositorio (si no existe)
git clone https://github.com/ezraidenn/DEBUGBI0.git
cd DEBUGBI0

# ⬜ 1.3 Ejecutar script de setup
chmod +x deployment/setup-server.sh
sudo ./deployment/setup-server.sh
```

**Resultado esperado:**
- Usuario `deploy` creado
- Directorio `/var/www/biostar-monitor/` creado
- Servicio systemd instalado
- Nginx configurado

**Verificar:**
```bash
sudo systemctl status biostar-monitor
sudo systemctl status nginx
ls -la /var/www/biostar-monitor/
```

---

### 2️⃣ Configurar Variables de Entorno

**Ubicación:** Servidor de producción (10.0.2.64)

```bash
# ⬜ 2.1 Editar archivo .env
sudo nano /var/www/biostar-monitor/shared/.env
```

**⬜ 2.2 Copiar esta configuración:**

```env
BIOSTAR_HOST=https://10.0.0.100
BIOSTAR_USER=rcetina
BIOSTAR_PASSWORD=aP1su.ser

SECRET_KEY=586de10a4e4af3e0267040987552b53a3af9f81f4cb20ba4c18d6f36eda16b93
FLASK_ENV=production
TEMPLATES_AUTO_RELOAD=false

DATABASE_URL=sqlite:///instance/biostar_users.db

REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=true

PORT=5000
HOST=0.0.0.0
DEBUG=false
```

**⬜ 2.3 Guardar:** `Ctrl+O`, `Enter`, `Ctrl+X`

**Verificar:**
```bash
cat /var/www/biostar-monitor/shared/.env
```

---

### 3️⃣ Generar SSH Keys

**Ubicación:** Servidor de producción (10.0.2.64)

```bash
# ⬜ 3.1 Generar par de claves
ssh-keygen -t ed25519 -C "github-actions-deploy" -f /tmp/biostar_deploy -N ""

# ⬜ 3.2 Configurar clave pública
sudo mkdir -p /home/deploy/.ssh
sudo cp /tmp/biostar_deploy.pub /home/deploy/.ssh/authorized_keys
sudo chown -R deploy:deploy /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
sudo chmod 600 /home/deploy/.ssh/authorized_keys

# ⬜ 3.3 Mostrar clave PRIVADA (cópiala COMPLETA)
cat /tmp/biostar_deploy
```

**⚠️ IMPORTANTE:** Copia TODA la clave (desde `-----BEGIN` hasta `-----END`)

**Verificar:**
```bash
ls -la /home/deploy/.ssh/
cat /home/deploy/.ssh/authorized_keys
```

---

### 4️⃣ Configurar GitHub Secrets

**Ubicación:** GitHub (navegador web)

**⬜ 4.1 Ir a:**
```
https://github.com/ezraidenn/DEBUGBI0/settings/secrets/actions
```

**⬜ 4.2 Crear Secret: `SSH_PRIVATE_KEY`**
- Click "New repository secret"
- Name: `SSH_PRIVATE_KEY`
- Secret: Pegar clave privada COMPLETA de `/tmp/biostar_deploy`
- Click "Add secret"

**⬜ 4.3 Crear Secret: `SERVER_HOST`**
- Click "New repository secret"
- Name: `SERVER_HOST`
- Secret: `10.0.2.64`
- Click "Add secret"

**⬜ 4.4 Crear Secret: `SERVER_USER`**
- Click "New repository secret"
- Name: `SERVER_USER`
- Secret: `deploy`
- Click "Add secret"

**Verificar:**
- Debes ver 3 secrets en la lista
- Los valores NO se muestran por seguridad (es normal)

---

### 5️⃣ Eliminar Clave Privada del Servidor (Seguridad)

**Ubicación:** Servidor de producción (10.0.2.64)

```bash
# ⬜ 5.1 Eliminar archivos temporales
rm /tmp/biostar_deploy
rm /tmp/biostar_deploy.pub

# ⬜ 5.2 Verificar que se eliminaron
ls /tmp/biostar_deploy*
# Debe decir: "No such file or directory"
```

---

### 6️⃣ Probar Auto-Deploy

**Ubicación:** Tu máquina Windows

**Opción A: Usar script de PowerShell**

```powershell
# ⬜ 6.1 Ejecutar script de prueba
cd C:\Users\Administrador\Documents\DebugBi0\DEBUGBI0
.\test_auto_deploy.ps1
```

**Opción B: Manual**

```bash
# ⬜ 6.1 Hacer un cambio pequeño
echo "# Test auto-deploy" >> README.md

# ⬜ 6.2 Commit
git add .
git commit -m "test: Probar auto-deploy"

# ⬜ 6.3 Push
git push origin main
```

**Opción C: Deploy manual desde GitHub**

```
⬜ 6.1 Ir a: https://github.com/ezraidenn/DEBUGBI0/actions
⬜ 6.2 Click en "Deploy to Production"
⬜ 6.3 Click en "Run workflow"
⬜ 6.4 Seleccionar rama "main"
⬜ 6.5 Click en "Run workflow"
```

---

### 7️⃣ Monitorear Deploy

**⬜ 7.1 Ver progreso en GitHub:**
```
https://github.com/ezraidenn/DEBUGBI0/actions
```

**⬜ 7.2 Ver logs en servidor:**
```bash
ssh tu_usuario@10.0.2.64
sudo journalctl -u biostar-monitor -f
```

**⬜ 7.3 Verificar estado:**
```bash
sudo systemctl status biostar-monitor
ls -lt /var/www/biostar-monitor/releases/
```

---

### 8️⃣ Verificar que Funciona

**⬜ 8.1 Abrir navegador:**
```
http://10.0.2.64
```

**⬜ 8.2 Login:**
- Usuario: `admin`
- Password: `admin123`

**⬜ 8.3 Verificar funcionalidad:**
- Dashboard carga correctamente
- Datos de BioStar se muestran
- No hay errores en consola

---

## 🎉 Checklist Final

Marca cada item cuando lo completes:

- [ ] 1. Servidor configurado (`setup-server.sh` ejecutado)
- [ ] 2. Variables de entorno configuradas (`.env` editado)
- [ ] 3. SSH keys generadas
- [ ] 4. GitHub Secrets configurados (3 secrets)
- [ ] 5. Clave privada eliminada del servidor
- [ ] 6. Primer deploy ejecutado
- [ ] 7. Deploy monitoreado (sin errores)
- [ ] 8. Aplicación funcionando en http://10.0.2.64

---

## 🚀 Después de Completar

Una vez que todos los items estén marcados:

### ✅ Auto-Deploy está ACTIVO

Cada vez que hagas:
```bash
git push origin main
```

Se ejecutará automáticamente:
1. Tests (si existen)
2. Build del artefacto
3. Upload al servidor
4. Deploy atómico
5. Restart del servicio

### 📊 Monitoreo

**Ver deploys en GitHub:**
```
https://github.com/ezraidenn/DEBUGBI0/actions
```

**Ver logs en servidor:**
```bash
sudo journalctl -u biostar-monitor -f
```

### 🔄 Rollback

Si algo sale mal:
```bash
ssh tu_usuario@10.0.2.64
cd /var/www/biostar-monitor
./deployment/rollback.sh
```

---

## 📚 Documentación

- **Guía completa:** `CONFIGURAR_AUTO_DEPLOY.md`
- **Deployment avanzado:** `DEPLOYMENT.md`
- **Inicio rápido:** `QUICKSTART.md`

---

## 🆘 Problemas Comunes

### ❌ Deploy falla en GitHub Actions

**Causa:** GitHub Secrets no configurados o incorrectos

**Solución:**
1. Verificar que los 3 secrets existan
2. Regenerar SSH keys si es necesario
3. Verificar IP del servidor

### ❌ Servicio no inicia en servidor

**Causa:** `.env` mal configurado o permisos incorrectos

**Solución:**
```bash
sudo journalctl -u biostar-monitor -n 100
cat /var/www/biostar-monitor/shared/.env
sudo chown -R deploy:deploy /var/www/biostar-monitor
```

### ❌ No se puede conectar a BioStar

**Causa:** Credenciales incorrectas o red

**Solución:**
```bash
ping 10.0.0.100
curl -k https://10.0.0.100
cat /var/www/biostar-monitor/shared/.env | grep BIOSTAR
```

---

**Última actualización:** Enero 2026
