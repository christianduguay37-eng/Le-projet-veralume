@echo off
chcp 65001 >nul
title Harnais d'Agentivité Souverain
cd /d "%~dp0"

echo ==============================================================================
echo           ⚡ DÉMARRAGE DU HARNAIS D'AGENTIVITÉ SOUVERAIN ⚡
echo ==============================================================================
echo.

:: Vérification de Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Python n'est pas détecté sur votre machine.
    echo Veuillez installer Python depuis https://www.python.org/ en cochant "Add to PATH".
    echo.
    pause
    exit /b 1
)

:: Lancement interactif du Harnais Souverain
python run_harness.py --profile default

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [INFO] Le programme s'est arrêté.
    pause
)
