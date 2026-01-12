#!/bin/bash
# Instalacion Completa Automatizada - BioStar Monitor
set -e

echo "=========================================="
echo "  BioStar Monitor - Instalacion Completa"
echo "=========================================="
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

APP_PATH="/var/www/biostar-monitor"
DEPLOY_USER="deploy"

echo -e "${CYAN}Paso 1: Ejecutando setup del servidor...${NC}"
if [ -f "deployment/setup-server.sh" ]; then
    chmod +x deployment/setup-server.sh
    sudo ./deployment/setup-server.sh
    echo -e "${GREEN}✓ Setup del servidor completado${NC}"
else
    echo -e "${RED}✗ Error: setup-server.sh no encontrado${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}Paso 2: Configurando variables de entorno...${NC}"
sudo tee ${APP_PATH}/shared/.env > /dev/null <<'EOF'
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
EOF

sudo chown deploy:deploy ${APP_PATH}/shared/.env
sudo chmod 600 ${APP_PATH}/shared/.env
echo -e "${GREEN}✓ Variables de entorno configuradas${NC}"

echo ""
echo -e "${CYAN}Paso 3: Generando SSH keys para GitHub Actions...${NC}"
if [ ! -f /tmp/biostar_deploy ]; then
    ssh-keygen -t ed25519 -C "github-actions-deploy" -f /tmp/biostar_deploy -N ""
    echo -e "${GREEN}✓ SSH keys generadas${NC}"
else
    echo -e "${YELLOW}⚠ SSH keys ya existen${NC}"
fi

sudo mkdir -p /home/${DEPLOY_USER}/.ssh
sudo cp /tmp/biostar_deploy.pub /home/${DEPLOY_USER}/.ssh/authorized_keys
sudo chown -R ${DEPLOY_USER}:${DEPLOY_USER} /home/${DEPLOY_USER}/.ssh
sudo chmod 700 /home/${DEPLOY_USER}/.ssh
sudo chmod 600 /home/${DEPLOY_USER}/.ssh/authorized_keys
echo -e "${GREEN}✓ SSH keys configuradas para usuario deploy${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}  ✓ INSTALACION COMPLETADA${NC}"
echo "=========================================="
echo ""
echo -e "${YELLOW}IMPORTANTE: Copia esta clave privada a GitHub Secrets${NC}"
echo ""
echo -e "${CYAN}Clave privada SSH (SSH_PRIVATE_KEY):${NC}"
echo "----------------------------------------"
cat /tmp/biostar_deploy
echo "----------------------------------------"
echo ""
echo -e "${YELLOW}Pasos siguientes:${NC}"
echo "1. Ve a: https://github.com/ezraidenn/DEBUGBI0/settings/secrets/actions"
echo "2. Crea estos secrets:"
echo "   - SSH_PRIVATE_KEY: (copia la clave de arriba)"
echo "   - SERVER_HOST: 10.0.2.64"
echo "   - SERVER_USER: deploy"
echo ""
echo -e "${CYAN}Verificar instalacion:${NC}"
echo "  sudo systemctl status biostar-monitor"
echo "  sudo systemctl status nginx"
echo ""
echo -e "${CYAN}Ver logs:${NC}"
echo "  sudo journalctl -u biostar-monitor -f"
echo ""
echo -e "${GREEN}¡Listo para recibir deployments automaticos!${NC}"
echo ""
