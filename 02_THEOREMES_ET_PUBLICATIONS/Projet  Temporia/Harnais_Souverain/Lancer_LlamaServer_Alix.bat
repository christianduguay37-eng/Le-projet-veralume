@echo off
chcp 65001 >nul
title Llama.cpp Server - Moteur Natif C++ (Vulkan GPU Arc 140V)
color 0B

echo ==============================================================================
echo        🦙 LLAMA.CPP SERVER — MOTEUR D'INFÉRENCE SOUVERAIN NATIF C++ ⚡
echo             Projet Temporia & Atelier Kairos — Lunar Lake 258V
echo ==============================================================================
echo.

set "VULKAN_SERVER=C:\Users\Christian\.lmstudio\extensions\backends\llama.cpp-win-x86_64-vulkan-avx2-2.27.1\llama-server.exe"
set "CPU_SERVER=C:\Users\Christian\Desktop\LOKI_Beta_Tester\llama-server.exe"

REM Choix du binaire (Vulkan GPU prioritaire, sinon CPU AVX2)
if exist "%VULKAN_SERVER%" (
    set "LLAMA_BIN=%VULKAN_SERVER%"
    echo [OK] Moteur Llama.cpp GPU Vulkan detecte (Intel Arc 140V).
) else if exist "%CPU_SERVER%" (
    set "LLAMA_BIN=%CPU_SERVER%"
    echo [OK] Moteur Llama.cpp CPU AVX2 detecte.
) else (
    echo [ERREUR] Aucun binaire llama-server.exe trouve.
    pause
    exit /b 1
)

REM Choix du modèle GGUF par défaut
set "DEFAULT_MODEL=C:\Users\Christian\Desktop\LOKI_Beta_Tester\kairos_model.gguf"
if not "%~1"=="" (
    set "MODEL_PATH=%~1"
) else (
    set "MODEL_PATH=%DEFAULT_MODEL%"
)

if not exist "%MODEL_PATH%" (
    echo [ERREUR] Modele GGUF introuvable : %MODEL_PATH%
    pause
    exit /b 1
)

echo [OK] Modele charge : %MODEL_PATH%
echo [OK] Serveur a l'ecoute sur http://127.0.0.1:8080 (API OpenAI /v1)
echo.
echo Pressez Ctrl+C pour arreter le serveur.
echo ==============================================================================
echo.

"%LLAMA_BIN%" -m "%MODEL_PATH%" --host 127.0.0.1 --port 8080 -c 4096 --cont-batching -ngl 99 --alias alix-llamacpp

pause
