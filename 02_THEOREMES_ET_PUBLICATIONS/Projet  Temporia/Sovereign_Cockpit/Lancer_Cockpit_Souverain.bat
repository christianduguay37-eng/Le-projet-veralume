@echo off
chcp 65001 > nul
title 👑 ALIX SOUVERAINE — COCKPIT D'ATELIER KAIROS
color 0B

echo ==========================================================================
echo        👑 DÉMARRAGE DU COCKPIT AGENTIQUE SOUVERAIN (ALIX MASTER) ⚡
echo             « Zéro Abonnement • Multi-Fournisseurs • 100%% Souverain »
echo ==========================================================================
echo.
echo  👉 URL Locale    : http://127.0.0.1:7777
echo  👉 Fournisseurs  : OpenRouter, Groq, DeepSeek, Cerebras, Google, Ollama
echo  👉 Télémétrie    : Intel Lunar Lake 258V + NPU 48 TOPS
echo.
echo ==========================================================================
echo  Ouverture de ton cockpit dans le navigateur...
echo ==========================================================================

cd /d "C:\Users\Christian\Documents\Exocerveau_Souverain_Master\Projet  Temporia\Sovereign_Cockpit"

REM Ouvre automatiquement le navigateur sur le cockpit
start "" cmd /c "timeout /t 2 /nobreak > nul && start http://127.0.0.1:7777"

REM Lance le serveur d'atelier
python sovereign_server.py
pause
