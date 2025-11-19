# 🚀 Guía Rápida - Debug BioStar

## Instalación en 3 pasos

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar credenciales
Editar el archivo `.env` con tus credenciales:
```env
BIOSTAR_HOST=https://10.0.0.100
BIOSTAR_USER=tu_usuario
BIOSTAR_PASSWORD=tu_password
```

### 3. Probar conexión
```bash
python quick_test.py
```

---

## 🎯 Uso Básico

### Ejecutar el sistema completo
```bash
python src/main.py
```

Esto abrirá un menú interactivo con las siguientes opciones:
1. **Listar todos los checadores** - Ver todos los dispositivos conectados
2. **Ver debug del día** - Obtener logs de un checador específico
3. **Asignar alias** - Dar nombres personalizados a los checadores
4. **Exportar todo** - Generar reportes Excel de todos los checadores

---

## 📝 Ejemplos de Código

### Listar dispositivos
```python
from src.api.device_monitor import DeviceMonitor

monitor = DeviceMonitor()
monitor.login()

devices = monitor.get_all_devices()
for device in devices:
    print(f"{device['id']} - {device['name']}")
```

### Obtener debug del día
```python
# Obtener resumen rápido
summary = monitor.get_debug_summary(device_id=12345)
print(f"Total eventos: {summary['total_events']}")

# Exportar a Excel
monitor.export_daily_debug(device_id=12345)
```

### Asignar alias a un checador
```python
monitor.set_device_alias(
    device_id=12345,
    alias="Entrada Principal",
    location="Planta Baja",
    notes="Checador principal"
)
```

---

## 📊 Códigos de Eventos Comunes

| Código | Descripción |
|--------|-------------|
| 4864   | ✅ Acceso concedido |
| 4865   | ❌ Acceso denegado |
| 20736  | 🚨 Puerta forzada |
| 28672  | 🔌 Dispositivo conectado |
| 28673  | 🔌 Dispositivo desconectado |

---

## 📁 Estructura de Archivos

```
debug biostar para checadores/
├── src/
│   ├── api/
│   │   ├── biostar_client.py      # Cliente de API
│   │   └── device_monitor.py      # Monitor de dispositivos
│   ├── utils/
│   │   ├── config.py              # Configuración
│   │   └── logger.py              # Logs
│   └── main.py                    # Script principal
├── config/
│   └── device_aliases.json        # Aliases de checadores
├── data/outputs/                  # Reportes generados
├── examples/                      # Ejemplos de uso
├── .env                           # Credenciales
└── quick_test.py                  # Test rápido
```

---

## 🔧 Solución de Problemas

### Error de autenticación
- Verifica que las credenciales en `.env` sean correctas
- Asegúrate de que el host sea accesible (ping al servidor)

### No se encuentran dispositivos
- Verifica que haya dispositivos configurados en BioStar
- Revisa los permisos del usuario

### Error SSL
- El sistema ya desactiva la verificación SSL por defecto
- Si persiste, verifica la conectividad de red

---

## 💡 Tips

1. **Alias personalizados**: Usa nombres descriptivos para identificar fácilmente cada checador
2. **Exportación diaria**: Programa el script para exportar automáticamente cada día
3. **Monitoreo**: Revisa los logs regularmente para detectar problemas
4. **Backup**: Los archivos Excel se guardan en `data/outputs/`

---

## 📞 Soporte

Para más información:
- Ver `README.md` para documentación completa
- Revisar `examples/ejemplo_basico.py` para más ejemplos
- Documentación oficial: https://bs2api.biostar2.com/
