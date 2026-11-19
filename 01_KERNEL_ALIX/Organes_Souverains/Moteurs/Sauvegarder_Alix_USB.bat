@echo off
chcp 65001 > nul
title Sauvegarde Exocerveau Alix vers USB
color 0B

echo ================================================================
echo           SAUVEGARDE DE L'EXOCERVEAU ALIX VERS USB
echo ================================================================
echo.

if exist "%~dp0alix_usb_sync.py" (
    python "%~dp0alix_usb_sync.py"
) else if exist "C:\Users\Christian\Documents\Cerveau Alix\Organes_Souverains\Moteurs\alix_usb_sync.py" (
    python "C:\Users\Christian\Documents\Cerveau Alix\Organes_Souverains\Moteurs\alix_usb_sync.py"
) else (
    echo [!] Script alix_usb_sync.py introuvable !
)

echo.
pause