# 🤖 PROMPT PARA WINDSURF - INSTALACIÓN AUTOMÁTICA DEL SERVIDOR

Copia y pega este prompt completo en Windsurf del servidor para que haga toda la instalación automáticamente.

---

## 📋 PROMPT PARA WINDSURF

```
Necesito que configures completamente el servidor para recibir deployments automáticos desde GitHub. Este es un sistema de monitoreo BioStar con CI/CD profesional usando GitHub Actions y systemd.

CONTEXTO:
- Repositorio: https://github.com/ezraidenn/DEBUGBI0
- Servidor: Ubuntu/Debian Linux
- IP del servidor: 10.0.2.64
- Usuario de deployment: deploy
- Ruta de instalación: /var/www/biostar-monitor

TAREAS A REALIZAR (EN ORDEN):

1. CLONAR REPOSITORIO
   - Clonar desde https://github.com/ezraidenn/DEBUGBI0.git
   - Ubicación: directorio actual o /tmp/DEBUGBI0

2. EJECUTAR SCRIPT DE SETUP
   - Dar permisos de ejecución a deployment/setup-server.sh
   - Ejecutar con sudo: sudo ./deployment/setup-server.sh
   - Este script creará:
     * Usuario 'deploy'
     * Estructura de directorios en /var/www/biostar-monitor/
     * Instalará Python3, pip, venv, nginx, rsync
     * Configurará servicio systemd
     * Configurará nginx como reverse proxy
     * Configurará sudoers para restart sin password

3. CONFIGURAR VARIABLES DE ENTORNO
   - Editar /var/www/biostar-monitor/shared/.env
   - Configurar con estos valores:
     
     BIOSTAR_URL=https://10.0.0.100
     BIOSTAR_USERNAME=admin
     BIOSTAR_PASSWORD=SOLICITAR_AL_USUARIO
     
     FLASK_SECRET_KEY=GENERAR_ALEATORIO_64_CHARS
     FLASK_ENV=production
     DEBUG=False
     
     DATABASE_URL=sqlite:///instance/biostar_users.db
     
     SESSION_COOKIE_SECURE=True
     SESSION_COOKIE_HTTPONLY=True
     SESSION_COOKIE_SAMESITE=Lax
     
     HOST=0.0.0.0
     PORT=5000
   
   - Para FLASK_SECRET_KEY, generar usando: python3 -c "import secrets; print(secrets.token_hex(32))"
   - IMPORTANTE: Solicitar al usuario la contraseña de BioStar antes de continuar

4. CONFIGURAR SSH PARA GITHUB ACTIONS
   - Generar par de claves SSH para deployment:
     ssh-keygen -t ed25519 -C "github-actions-deploy" -f /tmp/biostar_deploy -N ""
   
   - Copiar clave pública al usuario deploy:
     sudo mkdir -p /home/deploy/.ssh
     sudo cp /tmp/biostar_deploy.pub /home/deploy/.ssh/authorized_keys
     sudo chown -R deploy:deploy /home/deploy/.ssh
     sudo chmod 700 /home/deploy/.ssh
     sudo chmod 600 /home/deploy/.ssh/authorized_keys
   
   - Mostrar clave PRIVADA al usuario para que la agregue a GitHub Secrets:
     cat /tmp/biostar_deploy
   
   - Explicar que debe ir a:
     https://github.com/ezraidenn/DEBUGBI0/settings/secrets/actions
     Y crear estos secrets:
     * SSH_PRIVATE_KEY: (contenido completo de /tmp/biostar_deploy)
     * SERVER_HOST: 10.0.2.64
     * SERVER_USER: deploy

5. VERIFICAR INSTALACIÓN
   - Verificar que el servicio systemd está instalado:
     sudo systemctl status biostar-monitor
   
   - Verificar que nginx está corriendo:
     sudo systemctl status nginx
   
   - Verificar estructura de directorios:
     ls -la /var/www/biostar-monitor/
     ls -la /var/www/biostar-monitor/shared/
   
   - Verificar permisos:
     ls -la /home/deploy/.ssh/

6. PREPARAR PARA PRIMER DEPLOYMENT
   - Explicar al usuario que debe:
     a) Agregar los GitHub Secrets (SSH_PRIVATE_KEY, SERVER_HOST, SERVER_USER)
     b) Ir a https://github.com/ezraidenn/DEBUGBI0/actions
     c) Click en "Deploy to Production"
     d) Click en "Run workflow"
     e) Seleccionar rama "main"
     f) Click en "Run workflow"
   
   - O simplemente hacer push a main desde su máquina de desarrollo

7. MOSTRAR RESUMEN FINAL
   - Mostrar checklist de lo completado
   - Mostrar comandos útiles para monitoreo:
     * Ver logs: sudo journalctl -u biostar-monitor -f
     * Estado: sudo systemctl status biostar-monitor
     * Reiniciar: sudo systemctl restart biostar-monitor
     * Ver releases: ls -lt /var/www/biostar-monitor/releases/
     * Rollback: cd /var/www/biostar-monitor && ./deployment/rollback.sh
   
   - URL de acceso: http://10.0.2.64
   - Credenciales por defecto: admin / admin123

IMPORTANTE:
- Ejecutar todos los comandos con sudo cuando sea necesario
- Verificar cada paso antes de continuar al siguiente
- Si algún paso falla, mostrar el error y sugerir solución
- Al final, mostrar un resumen completo de lo configurado
- Incluir la clave privada SSH para que el usuario la copie a GitHub

NOTAS DE SEGURIDAD:
- La clave privada SSH solo debe mostrarse UNA VEZ y luego debe eliminarse del servidor
- Recordar al usuario eliminar /tmp/biostar_deploy después de copiarla a GitHub
- El archivo .env contiene credenciales sensibles y no debe exponerse

¿Entendido? Procede con la instalación paso a paso, mostrando el progreso de cada tarea.
```

---

## 📝 INSTRUCCIONES PARA EL USUARIO

1. **Conectarse al servidor:**
   ```bash
   ssh tu_usuario@10.0.2.64
   ```

2. **Abrir Windsurf en el servidor**

3. **Copiar y pegar el PROMPT completo de arriba**

4. **Windsurf ejecutará automáticamente:**
   - Clonación del repositorio
   - Instalación de dependencias
   - Configuración del servicio systemd
   - Configuración de Nginx
   - Generación de SSH keys
   - Configuración de .env

5. **Cuando Windsurf te muestre la clave privada SSH:**
   - Cópiala COMPLETA (incluyendo `-----BEGIN` y `-----END`)
   - Ve a: https://github.com/ezraidenn/DEBUGBI0/settings/secrets/actions
   - Crea el secret `SSH_PRIVATE_KEY` con esa clave
   - Crea el secret `SERVER_HOST` con valor: `10.0.2.64`
   - Crea el secret `SERVER_USER` con valor: `deploy`

6. **Ejecutar primer deployment:**
   - Ve a: https://github.com/ezraidenn/DEBUGBI0/actions
   - Click en "Deploy to Production"
   - Click en "Run workflow"
   - Selecciona rama "main"
   - Click en "Run workflow"

7. **Verificar:**
   - Espera ~2 minutos
   - Accede a: http://10.0.2.64
   - Login: `admin` / `admin123`

---

## 🔐 DATOS QUE NECESITARÁS TENER A MANO

Antes de ejecutar el prompt, ten listos:

1. **Contraseña de BioStar 2:**
   - Usuario: admin
   - Password: [TU_PASSWORD_AQUI]

2. **Acceso a GitHub:**
   - Para configurar los secrets

---

## ✅ RESULTADO ESPERADO

Después de que Windsurf termine, tendrás:

✅ Servidor completamente configurado  
✅ Servicio systemd instalado y habilitado  
✅ Nginx configurado como reverse proxy  
✅ Estructura de directorios creada  
✅ Usuario `deploy` configurado  
✅ SSH keys generadas  
✅ Archivo `.env` configurado  
✅ Sistema listo para recibir deployments automáticos  

**Cada push a `main` desplegará automáticamente en el servidor.**

---

## 🆘 SI ALGO FALLA

Si Windsurf tiene problemas, puedes ejecutar manualmente:

```bash
# Clonar repo
git clone https://github.com/ezraidenn/DEBUGBI0.git
cd DEBUGBI0

# Ejecutar setup
chmod +x deployment/setup-server.sh
sudo ./deployment/setup-server.sh

# Seguir instrucciones de QUICKSTART.md
cat QUICKSTART.md
```

---

**Última actualización:** Enero 2026
