# Navegar al directorio del proyecto
Set-Location "D:\Users\Ikaros\Desktop\PLAYGROUND\stumble-xbox"

# Eliminar entorno virtual si existe
if (Test-Path ".venv") {
    Write-Host "Eliminando entorno virtual existente..."
    Remove-Item ".venv" -Recurse -Force
}

# Crear nuevo entorno virtual
Write-Host "Creando nuevo entorno virtual..."
python -m venv .venv

# Activar entorno virtual
Write-Host "Activando entorno virtual..."
& ".venv\Scripts\Activate.ps1"

# Actualizar pip, setuptools y wheel
Write-Host "Actualizando pip, setuptools y wheel..."
pip install --upgrade pip setuptools wheel

# Instalar paquetes requeridos
Write-Host "Instalando paquetes..."
pip install `
    opencv-python==4.8.1.78 `
    pyautogui==0.9.54 `
    pygetwindow==0.0.9 `
    Pillow==10.0.1 `
    numpy==1.26.4 `
    keyboard==0.13.5

# Verificar instalación
Write-Host "`n✅ Instalación completada. Paquetes instalados:"
pip list | Select-String "opencv|pyautogui|pygetwindow|Pillow|numpy|keyboard"