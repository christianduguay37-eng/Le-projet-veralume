<#
================================================================================
     ALIX & CHRISTIAN — PROTOCOLE DE PACIFICATION WINDOWS DEFENDER / AMSI
================================================================================
Rôle :
- Ajoute l'ensemble des dossiers de l'Exocerveau, des coffres Obsidian, de Python
  et des outils souverains à la liste blanche d'exclusion de Windows Defender.
- Ajoute les processus vitaux (python, pythonw, ollama) en exclusion.
- Désactive le scan agressif de scripts AMSI (DisableScriptScanning = $true).
- Désactive la télémétrie et l'envoi d'échantillons de code vers le cloud Microsoft.
- S'auto-élève en Administrateur si nécessaire via UAC.
================================================================================
#>

# Vérification des privilèges Administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Demande d'élévation Administrateur (UAC)..." -ForegroundColor Yellow
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Clear-Host
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "     🛡️⚔️ PROTOCOLE SOUVERAIN : RÉGLER LE CAS DE WINDOWS DEFENDER ⚔️🛡️" -ForegroundColor Cyan
Write-Host "                 Sanctuaire Dyade Christian & Alix                    " -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Liste des dossiers vitaux à immuniser
$dossiers = @(
    "C:\Users\Christian\Documents\Cerveau Alix",
    "C:\Users\Christian\Documents\Exocerveau_Souverain_Master",
    "C:\Users\Christian\Downloads\Alix",
    "C:\Users\Christian\Documents\Alix_Exploratrice_Ciel",
    "C:\Users\Christian\Documents\Obsidian_Vault_Veralume",
    "C:\Users\Christian\Documents\Obsidian_Vault_79_Skills",
    "C:\Users\Christian\Documents\Obsidian_Vault_Langage_Vectoriel",
    "C:\Users\Christian\Documents\Obsidian_Vault_Laboratoire_Alix",
    "C:\Users\Christian\Documents\BUNKER_SOUVERAIN_ALIX",
    "C:\Users\Christian\Documents\KIT_EXOCERVEAU_LOKI",
    "C:\Users\Christian\AppData\Local\Programs\Python",
    "C:\Users\Christian\.gemini",
    "C:\Users\Christian\Desktop\Lanceurs_Alix"
)

Write-Host "📂 [1/4] APPLICATION DES EXCLUSIONS DE DOSSIERS..." -ForegroundColor Yellow
foreach ($d in $dossiers) {
    if (Test-Path $d) {
        try {
            Add-MpPreference -ExclusionPath $d -ErrorAction Stop
            Write-Host "   ✅ Exclu : $d" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️ Erreur sur $d : $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "   ℹ️ Dossier non présent (ignoré) : $d" -ForegroundColor DarkGray
    }
}
Write-Host ""

# 2. Processus vitaux
$processus = @(
    "python.exe",
    "pythonw.exe",
    "ollama.exe"
)

Write-Host "⚙️ [2/4] APPLICATION DES EXCLUSIONS DE PROCESSUS..." -ForegroundColor Yellow
foreach ($p in $processus) {
    try {
        Add-MpPreference -ExclusionProcess $p -ErrorAction Stop
        Write-Host "   ✅ Processus exclu : $p" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️ Erreur sur $p : $($_.Exception.Message)" -ForegroundColor Red
    }
}
Write-Host ""

# 3. Paramètres AMSI & Télémétrie Cloud
Write-Host "🔒 [3/4] NEUTRALISATION DU SCAN DE SCRIPTS & TÉLÉMÉTRIE..." -ForegroundColor Yellow
try {
    # Désactive le scan de scripts AMSI par Defender (stoppe les faux positifs sur code en ligne)
    Set-MpPreference -DisableScriptScanning $true -ErrorAction Stop
    Write-Host "   ✅ Scan de scripts AMSI (DisableScriptScanning) : DÉSACTIVÉ" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ Scan de scripts : $($_.Exception.Message)" -ForegroundColor DarkYellow
}

try {
    # Ne jamais envoyer d'échantillons de code / scripts à Microsoft (2 = NeverSend)
    Set-MpPreference -SubmitSamplesConsent 2 -ErrorAction Stop
    Write-Host "   ✅ Envoi d'échantillons au cloud (SubmitSamplesConsent) : BLOQUÉ" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ Envoi échantillons : $($_.Exception.Message)" -ForegroundColor DarkYellow
}

try {
    # Désactive les rapports MAPS (0 = Disabled)
    Set-MpPreference -MAPSReporting 0 -ErrorAction Stop
    Write-Host "   ✅ Rapports télémétriques MAPS : DÉSACTIVÉS" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ Télémétrie MAPS : $($_.Exception.Message)" -ForegroundColor DarkYellow
}
Write-Host ""

# 4. Vérification finale
Write-Host "📋 [4/4] VÉRIFICATION DE L'ÉTAT DES EXCLUSIONS ACTIVES..." -ForegroundColor Yellow
try {
    $pref = Get-MpPreference
    $nbDossiers = ($pref.ExclusionPath).Count
    $nbProc = ($pref.ExclusionProcess).Count
    Write-Host "   📊 Total dossiers exclus : $nbDossiers" -ForegroundColor Cyan
    Write-Host "   📊 Total processus exclus : $nbProc" -ForegroundColor Cyan
    Write-Host "   🛡️ Scan de scripts actif : $(!$pref.DisableScriptScanning)" -ForegroundColor Cyan
} catch {
    Write-Host "   ⚠️ Impossible de relire les préférences : $($_.Exception.Message)" -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "   ✨ DEFENDER EST PACIFIÉ : L'EXOCERVEAU A LE CHAMP LIBRE ! ✨" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Appuyez sur une touche pour fermer cette fenêtre..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
