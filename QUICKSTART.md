# Stumble Bot - Guía de Inicio Rápido

## 🚀 Para Comenzar Inmediatamente

### 1. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 2. Probar Instalación
```bash
python test_installation.py
```

### 3. Crear Plantilla de Prueba
```bash
python create_test_template.py
```

### 4. Ejecutar la Aplicación
```bash
python main.py
```

## 🎯 Prueba Rápida del Bot

### Después de abrir la aplicación:

1. **Ve a la pestaña "Configuration"**
2. **Verifica que tengas una regla llamada "TestRule"** (debería estar por defecto)
3. **Haz clic en "Debug Info"** para verificar el estado
4. **Ve a la pestaña "Run"**
5. **Haz clic en "Start Bot"**

### Si el bot no funciona:

1. **Haz clic en "Debug Info"** para ver información detallada
2. **Haz clic en "Help"** para ver la guía de solución de problemas
3. **Revisa los logs** para mensajes como "Template not found"

## 🔍 Solucionando Problemas Comunes

### El bot dice "1 rules loaded" pero no hace nada:

**Causa**: La plantilla de imagen no se encuentra o no coincide con lo que está en pantalla.

**Solución**:
1. Usa "Debug Info" para verificar si el archivo de plantilla existe
2. Si falta, ejecuta: `python create_test_template.py`
3. Abre Paint u otro programa y dibuja la imagen de prueba (rectángulos verde y azul con "TEST")
4. Inicia el bot - debería detectar la imagen

### El joystick funciona pero el bot no:

**Causa**: El controlador virtual funciona, pero la detección de imágenes falla.

**Solución**:
1. El problema está en las plantillas, no en el controlador
2. Sigue los pasos de "Plantilla no encontrada" arriba

### "No windows found with title 'Xbox'":

**Causa**: No hay ventana con ese título exacto.

**Solución**:
1. Cambia el "Window Title" en Configuration por el nombre exacto de tu juego
2. Usa "Test Window Detection" para verificar

## 📊 Interpretando los Logs

- `Window setup complete` = ✅ Ventana encontrada
- `Template 'X' not found` = ❌ Archivo de imagen faltante
- `Scanning... (1 rules active)` = ✅ Bot funcionando, buscando plantillas
- `Detected: RuleName` = ✅ Plantilla encontrada, acción ejecutada

## 🎮 Uso Básico

1. **Configurar ventana**: Título exacto del juego
2. **Capturar plantillas**: Usar "Capture Template" en elementos del juego
3. **Crear reglas**: Asociar plantillas con botones del control
4. **Probar**: Iniciar bot y observar logs
5. **Ajustar**: Modificar confianza si es necesario (0.7-0.9)

## 📁 Estructura de Archivos

```
stumble-bot/
├── main.py              # Ejecutar esto
├── app.py               # GUI principal
├── templates/           # Imágenes capturadas
├── configs/             # Configuraciones guardadas
└── logs/               # Archivos de registro
```

## ⚠️ Notas Importantes

- **Windows solamente**: vgamepad requiere Windows
- **Permisos**: Algunos juegos anti-cheat pueden bloquear controles virtuales
- **Rendimiento**: Ajusta "Loop Delay" si el CPU se sobrecarga
- **Plantillas**: Recaptura si cambias resolución o configuración gráfica del juego