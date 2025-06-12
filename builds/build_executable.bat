@echo off
echo ========================================
echo  CONSTRUCTOR DE EJECUTABLE VOLUME CONTROLLER
echo ========================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo Por favor instala Python desde https://python.org
    pause
    exit /b 1
)

echo Python detectado correctamente
echo.

REM Verificar si pip está disponible
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip no está disponible
    pause
    exit /b 1
)

echo pip detectado correctamente
echo.

REM Instalar dependencias si no están instaladas
echo Verificando e instalando dependencias...
pip install pyinstaller opencv-python mediapipe numpy pyautogui

echo.
echo Iniciando construcción del ejecutable...
echo.

REM Ejecutar el script de construcción
python build_volume_controller.py

echo.
echo Presiona cualquier tecla para continuar...
pause >nul 