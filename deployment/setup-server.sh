#!/bin/bash
# Script de configuración inicial del servidor para deployment
# Ejecutar UNA VEZ en el servidor de producción

set -e

APP_NAME="biostar-monitor"
APP_PATH="/var/www/${APP_NAME}"
DEPLOY_USER="deploy"

echo "🚀 Configurando servidor para ${APP_NAME}..."

# 1. Crear usuario de deployment (si no existe)
if ! id "$DEPLOY_USER" &>/dev/null; then
    echo "👤 Creando usuario ${DEPLOY_USER}..."
    sudo useradd -m -s /bin/bash ${DEPLOY_USER}
    echo "✅ Usuario ${DEPLOY_USER} creado"
else
    echo "✅ Usuario ${DEPLOY_USER} ya existe"
fi

# 2. Crear estructura de directorios
echo "📁 Creando estructura de directorios..."
sudo mkdir -p ${APP_PATH}/{releases,shared/{logs,instance,uploads}}
sudo chown -R ${DEPLOY_USER}:${DEPLOY_USER} ${APP_PATH}
echo "✅ Estructura creada en ${APP_PATH}"

# 3. Instalar dependencias del sistema
echo "📦 Instalando dependencias del sistema..."
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    rsync \
    git

echo "✅ Dependencias instaladas"

# 4. Configurar .env en shared (template)
if [ ! -f "${APP_PATH}/shared/.env" ]; then
    echo "📝 Creando template de .env..."
    sudo tee ${APP_PATH}/shared/.env > /dev/null << 'EOF'
# BioStar Configuration
BIOSTAR_URL=https://10.0.0.100
BIOSTAR_USERNAME=admin
BIOSTAR_PASSWORD=changeme

# Flask Configuration
FLASK_SECRET_KEY=changeme-generate-random-key
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
EOF
    sudo chown ${DEPLOY_USER}:${DEPLOY_USER} ${APP_PATH}/shared/.env
    echo "⚠️  IMPORTANTE: Edita ${APP_PATH}/shared/.env con tus credenciales reales"
else
    echo "✅ .env ya existe"
fi

# 5. Instalar servicio systemd
echo "⚙️  Instalando servicio systemd..."
sudo cp deployment/systemd/biostar-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable biostar-monitor
echo "✅ Servicio systemd instalado y habilitado"

# 6. Configurar sudoers para restart sin password
echo "🔐 Configurando sudoers para ${DEPLOY_USER}..."
sudo tee /etc/sudoers.d/${APP_NAME} > /dev/null << EOF
# Permitir a ${DEPLOY_USER} reiniciar el servicio sin password
${DEPLOY_USER} ALL=(ALL) NOPASSWD: /bin/systemctl restart ${APP_NAME}
${DEPLOY_USER} ALL=(ALL) NOPASSWD: /bin/systemctl status ${APP_NAME}
${DEPLOY_USER} ALL=(ALL) NOPASSWD: /bin/systemctl stop ${APP_NAME}
${DEPLOY_USER} ALL=(ALL) NOPASSWD: /bin/systemctl start ${APP_NAME}
EOF
sudo chmod 0440 /etc/sudoers.d/${APP_NAME}
echo "✅ Sudoers configurado"

# 7. Configurar SSH key para GitHub Actions
echo "🔑 Configurando SSH para deployment..."
sudo -u ${DEPLOY_USER} mkdir -p /home/${DEPLOY_USER}/.ssh
sudo -u ${DEPLOY_USER} chmod 700 /home/${DEPLOY_USER}/.ssh
echo "⚠️  IMPORTANTE: Agrega la clave pública de GitHub Actions a:"
echo "   /home/${DEPLOY_USER}/.ssh/authorized_keys"

# 8. Configurar Nginx (reverse proxy)
echo "🌐 Configurando Nginx..."
sudo tee /etc/nginx/sites-available/${APP_NAME} > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;  # Cambiar por tu dominio

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (para SSE)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    location /static {
        alias /var/www/biostar-monitor/current/webapp/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/${APP_NAME} /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
echo "✅ Nginx configurado"

# 9. Resumen
echo ""
echo "========================================="
echo "✅ Configuración del servidor completada"
echo "========================================="
echo ""
echo "📋 Próximos pasos:"
echo ""
echo "1. Edita las credenciales en:"
echo "   ${APP_PATH}/shared/.env"
echo ""
echo "2. Agrega la SSH key pública de GitHub Actions a:"
echo "   /home/${DEPLOY_USER}/.ssh/authorized_keys"
echo ""
echo "3. Configura los siguientes secrets en GitHub:"
echo "   - SSH_PRIVATE_KEY: Clave privada SSH para deployment"
echo "   - SERVER_HOST: IP o dominio del servidor"
echo "   - SERVER_USER: ${DEPLOY_USER}"
echo ""
echo "4. Haz push a la rama 'main' para activar el deployment automático"
echo ""
echo "📍 Estructura creada:"
echo "   ${APP_PATH}/releases/     → Releases versionados"
echo "   ${APP_PATH}/current/      → Symlink al release activo"
echo "   ${APP_PATH}/shared/       → Archivos compartidos (.env, logs, DB)"
echo ""
echo "🎉 ¡Listo para recibir deployments!"
