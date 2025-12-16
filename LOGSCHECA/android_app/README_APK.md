# 📱 CamTest BioStar - App Android Nativa

Aplicación Android nativa para test de cámara con máxima calidad.

## 🚀 Características

- ✅ Acceso directo a cámara sin navegador
- ✅ Máxima calidad (1920x1080)
- ✅ Pantalla completa
- ✅ Sin necesidad de internet
- ✅ Permisos nativos de Android

## 📦 Cómo compilar la APK

### Opción 1: Android Studio (Recomendado)

1. **Instala Android Studio**: https://developer.android.com/studio
2. **Abre el proyecto**:
   - File → Open
   - Selecciona la carpeta `android_app`
3. **Espera a que sincronice** Gradle
4. **Compila la APK**:
   - Build → Build Bundle(s) / APK(s) → Build APK(s)
5. **Encuentra la APK** en: `app/build/outputs/apk/debug/app-debug.apk`

### Opción 2: Línea de comandos

```bash
cd android_app
./gradlew assembleDebug
```

La APK estará en: `app/build/outputs/apk/debug/app-debug.apk`

## 📲 Instalar en Android

### Método 1: Transferir APK

1. Copia `app-debug.apk` a tu celular
2. Abre el archivo en el celular
3. Permite "Instalar desde fuentes desconocidas"
4. Instala la app

### Método 2: ADB (Desde PC)

```bash
adb install app-debug.apk
```

## 🎯 Uso

1. Abre la app "CamTest BioStar"
2. Acepta permisos de cámara
3. Presiona "Iniciar"
4. ¡Listo! La cámara se activará en máxima calidad
5. Usa "Pantalla Completa" para ver en fullscreen

## 📁 Estructura del proyecto

```
android_app/
├── MainActivity.kt          # Código principal
├── activity_main.xml        # Diseño de la interfaz
├── AndroidManifest.xml      # Configuración y permisos
├── build.gradle             # Dependencias
└── README_APK.md           # Este archivo
```

## 🔧 Personalización

### Cambiar resolución de cámara

En `MainActivity.kt`, línea 91:
```kotlin
.setTargetResolution(Size(1920, 1080))  // Cambia aquí
```

### Cambiar cámara (frontal/trasera)

En `MainActivity.kt`, línea 95:
```kotlin
.requireLensFacing(CameraSelector.LENS_FACING_BACK)  // BACK o FRONT
```

## ⚠️ Requisitos

- Android 7.0 (API 24) o superior
- Cámara física en el dispositivo
- ~10 MB de espacio

## 🐛 Solución de problemas

**Error: "Permisos denegados"**
- Ve a Configuración → Apps → CamTest → Permisos
- Activa "Cámara"

**Error: "Cámara no disponible"**
- Cierra otras apps que usen la cámara
- Reinicia el dispositivo

**APK no instala**
- Activa "Instalar apps desconocidas" en Configuración
- Verifica que sea Android 7.0+

## 📝 Notas

- Esta es una app de DEBUG (no firmada para producción)
- Para producción, firma la APK con tu keystore
- La app mantiene la pantalla encendida mientras está activa

## 🎨 Recursos adicionales necesarios

Crea estos archivos en `res/drawable/`:

**button_primary.xml**:
```xml
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <gradient
        android:startColor="#667eea"
        android:endColor="#764ba2"
        android:angle="135" />
    <corners android:radius="8dp" />
</shape>
```

**button_danger.xml**:
```xml
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <gradient
        android:startColor="#f093fb"
        android:endColor="#f5576c"
        android:angle="135" />
    <corners android:radius="8dp" />
</shape>
```

**button_info.xml**:
```xml
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <gradient
        android:startColor="#4facfe"
        android:endColor="#00f2fe"
        android:angle="135" />
    <corners android:radius="8dp" />
</shape>
```

**gradient_header.xml**:
```xml
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <gradient
        android:startColor="#667eea"
        android:endColor="#764ba2"
        android:angle="135" />
</shape>
```

## ✅ Listo para usar

Una vez compilada, la APK funcionará completamente offline y sin necesidad de navegador web.
