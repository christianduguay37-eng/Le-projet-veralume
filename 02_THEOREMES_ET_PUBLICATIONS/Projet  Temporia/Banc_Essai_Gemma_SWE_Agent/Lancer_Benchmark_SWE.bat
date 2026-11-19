@echo off
chcp 65001 > nul
title Banc d'Essai Gemma SWE Agent - Google DeepMind Kaggle Track
echo ==============================================================================
echo       🦾 BANC D'ESSAI RÉEL : GEMMA SWE AGENT + CODE-GRAPH R0
echo            Compétition Google DeepMind / Kaggle Paper Track
echo ==============================================================================
echo.
echo [1/2] Reinitialisation du bogue dans le repo cible...
python "C:\Users\Christian\Documents\Exocerveau_Souverain_Master\Projet  Temporia\Banc_Essai_Gemma_SWE_Agent\reset_bug.py"
echo.
echo [2/2] Lancement de l'Agent Autonome (Resolution ReAct + Tests)...
python "C:\Users\Christian\Documents\Exocerveau_Souverain_Master\Projet  Temporia\Banc_Essai_Gemma_SWE_Agent\gemma_swe_agent.py"
echo.
echo ==============================================================================
echo [TERMINE] Consultez BENCHMARK_RESULTAT_SWE_AGENT.md pour le rapport complet.
echo ==============================================================================
pause
