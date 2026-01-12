#!/bin/bash
# Script de rollback rápido
# Uso: ./rollback.sh [release_id]
# Si no se especifica release_id, vuelve al release anterior

set -e

APP_PATH="/var/www/biostar-monitor"
RELEASES_PATH="${APP_PATH}/releases"
CURRENT_LINK="${APP_PATH}/current"

# Obtener release actual
CURRENT_RELEASE=$(readlink ${CURRENT_LINK} | xargs basename)

if [ -z "$1" ]; then
    # No se especificó release, usar el anterior
    PREVIOUS_RELEASE=$(ls -t ${RELEASES_PATH} | grep -v ${CURRENT_RELEASE} | head -n 1)
    
    if [ -z "$PREVIOUS_RELEASE" ]; then
        echo "❌ No hay release anterior disponible"
        exit 1
    fi
    
    TARGET_RELEASE=$PREVIOUS_RELEASE
    echo "🔄 Rollback al release anterior: ${TARGET_RELEASE}"
else
    # Release específico
    TARGET_RELEASE=$1
    
    if [ ! -d "${RELEASES_PATH}/${TARGET_RELEASE}" ]; then
        echo "❌ Release ${TARGET_RELEASE} no existe"
        echo "Releases disponibles:"
        ls -t ${RELEASES_PATH}
        exit 1
    fi
    
    echo "🔄 Rollback al release: ${TARGET_RELEASE}"
fi

# Confirmar
echo "Release actual: ${CURRENT_RELEASE}"
echo "Target release: ${TARGET_RELEASE}"
read -p "¿Continuar con rollback? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Rollback cancelado"
    exit 1
fi

# Hacer rollback (cambiar symlink)
echo "🔗 Cambiando symlink..."
ln -sfn ${RELEASES_PATH}/${TARGET_RELEASE} ${CURRENT_LINK}

# Reiniciar servicio
echo "♻️  Reiniciando servicio..."
sudo systemctl restart biostar-monitor

# Verificar
sleep 2
if sudo systemctl is-active --quiet biostar-monitor; then
    echo "✅ Rollback exitoso!"
    echo "📍 Release activo: ${TARGET_RELEASE}"
else
    echo "❌ Error: El servicio no está corriendo"
    echo "Revisa los logs: sudo journalctl -u biostar-monitor -n 50"
    exit 1
fi
