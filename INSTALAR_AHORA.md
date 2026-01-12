# 🚀 INSTALACIÓN AUTOMÁTICA - UN SOLO COMANDO

## ⚡ Instalación Rápida (Recomendado)

### Opción 1: Desde Windows (Automático)

```powershell
# 1. Abrir PowerShell en este directorio
# 2. Ejecutar:
.\ejecutar_instalacion_completa.ps1
```

O simplemente **doble click** en: `INSTALAR_TODO.bat`

**El script hará TODO automáticamente:**
- ✅ Sube cambios a GitHub
- ✅ Se conecta al servidor (10.0.2.64)
- ✅ Clona el repositorio
- ✅ Ejecuta setup del servidor
- ✅ Configura variables de entorno
- ✅ Genera SSH keys
- ✅ Muestra la clave privada para GitHub

**Tiempo estimado:** 3-5 minutos

---

### Opción 2: Desde el Servidor Linux (Manual)

```bash
# 1. Conectarse al servidor
ssh tu_usuario@10.0.2.64

# 2. Ejecutar este comando (copia y pega TODO):
cd /tmp && \
rm -rf DEBUGBI0 && \
git clone https://github.com/ezraidenn/DEBUGBI0.git && \
cd DEBUGBI0 && \
chmod +x deployment/install_complete.sh && \
sudo ./deployment/install_complete.sh
```

**Eso es TODO.** El script hace el resto.

---

## 📋 Después de la Instalación

### 1️⃣ Configurar GitHub Secrets (2 minutos)

El script mostrará una **clave SSH privada**. Cópiala y:

1. Ve a: https://github.com/ezraidenn/DEBUGBI0/settings/secrets/actions
2. Click "New repository secret"
3. Crea estos 3 secrets:

| Name | Value |
|------|-------|
| `SSH_PRIVATE_KEY` | (pega la clave completa) |
| `SERVER_HOST` | `10.0.2.64` |
| `SERVER_USER` | `deploy` |

### 2️⃣ Activar Auto-Deploy (30 segundos)

```bash
# Hacer cualquier cambio y push
git add .
git commit -m "feat: Activar auto-deploy"
git push origin main
```

### 3️⃣ Verificar (1 minuto)

- **GitHub Actions:** https://github.com/ezraidenn/DEBUGBI0/actions
- **Aplicación:** http://10.0.2.64
- **Login:** admin / admin123

---

## ✅ ¡Listo!

Cada `git push` a `main` desplegará automáticamente.

---

## 🆘 Si Algo Falla

### Error: "Permission denied (publickey)"
**Solución:** Verifica que SSH_PRIVATE_KEY esté configurado correctamente en GitHub Secrets.

### Error: "Connection refused"
**Solución:** Verifica que el servidor esté accesible:
```bash
ping 10.0.2.64
ssh tu_usuario@10.0.2.64
```

### Ver logs del servidor
```bash
ssh tu_usuario@10.0.2.64
sudo journalctl -u biostar-monitor -f
```

---

## 📊 Comandos Útiles

### Ver estado del servicio
```bash
ssh tu_usuario@10.0.2.64 "sudo systemctl status biostar-monitor"
```

### Reiniciar servicio
```bash
ssh tu_usuario@10.0.2.64 "sudo systemctl restart biostar-monitor"
```

### Rollback
```bash
ssh tu_usuario@10.0.2.64 "cd /var/www/biostar-monitor && ./deployment/rollback.sh"
```

---

**Tiempo total de instalación:** ~5 minutos  
**Dificultad:** ⭐ Muy Fácil  
**Resultado:** Auto-deploy 100% funcional
