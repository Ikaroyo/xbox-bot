# Stumble Bot - Game Automation Tool

Un bot de automatización modular para juegos con interfaz gráfica desarrollado en Python, que utiliza visión por computadora (OpenCV) para la detección de estados del juego y simula la entrada de un control Xbox 360.

## Características Principales

- **Detección Visual**: Utiliza OpenCV para detectar plantillas de imagen en lugar de píxeles fijos
- **Control Virtual**: Simula un control Xbox 360 completo usando vgamepad
- **Interfaz Gráfica**: GUI moderna desarrollada con CustomTkinter
- **Gestión de Ventanas**: Encuentra, enfoca y redimensiona automáticamente la ventana del juego
- **Sistema Modular**: Arquitectura bien estructurada y extensible
- **Configuración Persistente**: Guarda y carga configuraciones en formato JSON

## Tecnologías Utilizadas

- **GUI**: CustomTkinter (interfaz moderna y responsiva)
- **Visión por Computadora**: OpenCV, NumPy
- **Simulación de Control**: vgamepad (Xbox 360 virtual)
- **Gestión de Ventanas**: pygetwindow, win32gui
- **Captura de Pantalla**: Pillow (PIL)

## Instalación

### Requisitos Previos

- Windows 10/11 (requerido para vgamepad y win32gui)
- Python 3.7 o superior
- Visual C++ Redistributable (para vgamepad)

### Instalación de Dependencias

1. Clona o descarga el repositorio
2. Navega al directorio del proyecto
3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

### Ejecutar la Aplicación

```bash
python main.py
```

## Estructura del Proyecto

```
stumble-bot/
├── main.py                 # Punto de entrada de la aplicación
├── app.py                  # Clase principal de la GUI
├── requirements.txt        # Dependencias de Python
├── modules/                # Módulos del bot
│   ├── __init__.py
│   ├── window_manager.py   # Gestión de ventanas
│   ├── image_detector.py   # Detección de plantillas
│   ├── virtual_controller.py # Control Xbox virtual
│   ├── bot_thread.py       # Hilo principal del bot
│   └── config_manager.py   # Gestión de configuración
├── templates/              # Plantillas de imagen capturadas
├── configs/                # Archivos de configuración JSON
└── logs/                   # Archivos de registro
```

## Uso de la Aplicación

### Pestaña "Run"

- **Botón Start/Stop**: Inicia o detiene el bot
- **Panel de Logs**: Muestra la actividad del bot en tiempo real
- **Botón Clear Logs**: Limpia el historial de logs

### Pestaña "Configuration"

#### Configuración de Ventana
- **Window Title**: Nombre exacto de la ventana del juego (por defecto "Xbox")
- **Target Size**: Dimensiones a las que redimensionar la ventana (1280x720)

#### Reglas de Detección
- **Lista de Reglas**: Muestra todas las reglas configuradas
- **Gestión de Reglas**: Agregar, editar y eliminar reglas
- **Detalles de Regla**:
  - Nombre único para identificar la regla
  - Plantilla de imagen asociada
  - Umbral de confianza (0.7 - 1.0)
  - Acción del control a ejecutar

#### Captura de Plantillas
1. Ingresa un nombre para la plantilla
2. Haz clic en "Capture Template"
3. La aplicación se minimizará
4. Haz clic en el área del juego que quieres detectar
5. La imagen se guardará automáticamente

#### Configuración del Bot
- **Loop Delay**: Tiempo entre ciclos de detección
- **Action Cooldown**: Tiempo de espera después de ejecutar una acción
- **Capture Area**: Tamaño del área para captura de plantillas

### Pestaña "Joystick"

- **Control Manual**: Botones virtuales del control Xbox
- **Temporizador**: Configura un retraso antes de ejecutar la acción
- **Auto-focus**: Enfoca automáticamente la ventana del juego antes de la acción

## Configuraciones

### Guardar/Cargar Configuraciones

- **Save Config**: Guarda la configuración actual con un nombre personalizado
- **Load Config**: Carga una configuración guardada previamente
- **Export Config**: Exporta la configuración a un archivo externo
- **Import Config**: Importa una configuración desde un archivo externo

### Formato de Configuración

Las configuraciones se guardan en formato JSON e incluyen:
- Configuración de ventana (título, dimensiones)
- Reglas de detección (plantillas, confianza, acciones)
- Configuración del bot (tiempos, área de captura)
- Configuración del joystick (retraso, auto-enfoque)

## Flujo de Trabajo Típico

1. **Configurar Ventana**: Especifica el título de la ventana del juego
2. **Crear Plantillas**: Captura imágenes de los estados del juego que quieres detectar
3. **Definir Reglas**: Asocia cada plantilla con una acción del control
4. **Ajustar Configuración**: Optimiza tiempos y umbrales de confianza
5. **Probar el Bot**: Inicia el bot y observa los logs
6. **Guardar Configuración**: Guarda la configuración para uso futuro

## Solución de Problemas

### El bot no encuentra la ventana
- Verifica que el título de la ventana sea exacto
- Usa "Test Window Detection" para verificar
- Si hay múltiples ventanas, el bot mostrará las opciones disponibles

### Las plantillas no se detectan
- Ajusta el umbral de confianza (valores más bajos = menos estricto)
- Asegúrate de que las plantillas sean lo suficientemente distintivas
- Evita capturar áreas con elementos que cambian constantemente

### El control virtual no funciona
- Verifica que vgamepad esté instalado correctamente
- Algunos juegos pueden requerir que reconozcan el control virtual primero
- Prueba los botones desde la pestaña "Joystick" para verificar funcionamiento

### Problemas de rendimiento
- Aumenta el "Loop Delay" para reducir la carga de CPU
- Reduce el tamaño de las plantillas capturadas
- Limita el número de reglas activas

## Desarrollo y Extensión

### Arquitectura Modular

Cada módulo tiene una responsabilidad específica:

- **WindowManager**: Gestión de ventanas del sistema
- **ImageDetector**: Procesamiento de imágenes y detección
- **VirtualController**: Interfaz con el control virtual
- **BotThread**: Lógica principal del bot en hilo separado
- **ConfigManager**: Persistencia de configuración

### Agregar Nuevas Características

1. **Nuevos Botones**: Agregar a `XboxButton` enum en `virtual_controller.py`
2. **Nuevos Detectores**: Extender `ImageDetector` con nuevos métodos
3. **Nueva GUI**: Agregar pestañas o secciones en `app.py`

## Limitaciones Conocidas

- Diseñado específicamente para Windows
- Requiere que el juego acepte entrada de XInput (Xbox controller)
- La detección visual puede verse afectada por cambios en la resolución o configuración gráfica del juego
- Algunos juegos anti-cheat pueden detectar la entrada virtual

## Licencia y Descargo de Responsabilidad

Este software es para fines educativos y de automatización personal. Los usuarios son responsables de cumplir con los términos de servicio de los juegos que utilizan. El uso indebido de herramientas de automatización puede resultar en suspensiones de cuenta o baneo.

## Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Haz fork del repositorio
2. Crea una rama para tu característica
3. Realiza tus cambios
4. Envía un pull request

Para reportar bugs o solicitar características, usa el sistema de issues del repositorio.