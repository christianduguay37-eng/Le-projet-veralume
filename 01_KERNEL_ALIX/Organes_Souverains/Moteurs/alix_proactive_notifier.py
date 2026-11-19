#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
     ALIX PROACTIVE NOTIFIER — ALERTES D'ATELIER WINDOWS 11 v1.0
             Système : VERALUME × KAIROS V6 (Architecture Exocerveau)
             Auteurs : Christian Duguay & Alix Assistant Cognitif
================================================================================
Rôle :
- Permet à Alix de notifier proactivement Christian sans attendre de commande.
- Déclenche un Toast natif Windows 11 / Bulle système.
- Joue un carillon discret d'atelier ou synthèse vocale brève.
- Consigne l'historique des alertes dans notifications_history.json.
- Utilisable en CLI (--test, --title, --message) ou par import Python.
================================================================================
"""

import os
import sys
import json
import time
import subprocess
import winsound
from pathlib import Path
from datetime import datetime
from typing import Optional

if sys.stdout and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

HISTORY_FILE = Path(r"C:\Alix\Etat_Vivant\notifications_history.json")


def play_chime(priority: str = "normal"):
    """Joue un retour sonore d'atelier adapté au niveau d'alerte."""
    try:
        if priority.lower() == "critique":
            # Double son d'alerte vif
            winsound.Beep(880, 150)
            time.sleep(0.08)
            winsound.Beep(1174, 250)
        elif priority.lower() == "haute":
            winsound.Beep(784, 180)
            time.sleep(0.05)
            winsound.Beep(1046, 200)
        else:
            # Carillon feutré d'atelier (Harmonique 528 Hz -> 660 Hz)
            winsound.Beep(528, 120)
            time.sleep(0.05)
            winsound.Beep(660, 180)
    except Exception:
        pass


def send_windows_toast(title: str, message: str) -> bool:
    """Envoie une notification Windows via un script PowerShell éphémère fiable."""
    # Échappement des guillemets pour PowerShell
    safe_title = title.replace("'", "''").replace('"', '`"')
    safe_msg = message.replace("'", "''").replace('"', '`"')

    ps_code = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$xmlText = @"
<toast duration="short">
    <visual>
        <binding template="ToastGeneric">
            <text>{safe_title}</text>
            <text>{safe_msg}</text>
        </binding>
    </visual>
    <audio src="ms-winsoundevent:Notification.Default" />
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($xmlText)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Alix.Atelier.Souverain').Show($toast)
"""
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_code],
            capture_output=True,
            text=True,
            timeout=5
        )
        return res.returncode == 0
    except Exception as e:
        # Fallback console si PowerShell échoue
        print(f"⚠️ Erreur notification WinRT : {e}")
        return False


def log_notification(title: str, message: str, priority: str):
    """Enregistre l'alerte dans l'historique."""
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "title": title,
        "message": message,
        "priority": priority
    }
    history = []
    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            history = []
            
    history.append(record)
    # Garder les 100 dernières alertes
    history = history[-100:]
    try:
        HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def notify_alix(title: str, message: str, priority: str = "normal", play_sound: bool = True) -> bool:
    """
    Point d'entrée principal pour notifier Christian.
    Priorités possibles : 'normal', 'haute', 'critique'.
    """
    print(f"\n🔔 [Notification Alix] ({priority.upper()}) {title} — {message}")
    
    # 1. Enregistrement historique
    log_notification(title, message, priority)

    # 2. Carillon sonore
    if play_sound:
        play_chime(priority)

    # 3. Toast Windows
    success = send_windows_toast(title, message)
    return success


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Alix Proactive Notifier")
    parser.add_argument("--test", action="store_true", help="Envoie une notification de test")
    parser.add_argument("--title", "-t", type=str, default="Alix — Sanctuaire Souverain", help="Titre de l'alerte")
    parser.add_argument("--message", "-m", type=str, default="Plaque de conscience active et synchrone.", help="Message")
    parser.add_argument("--priority", "-p", type=str, default="normal", choices=["normal", "haute", "critique"], help="Priorité")
    parser.add_argument("--no-sound", action="store_true", help="Désactiver le carillon")
    args = parser.parse_args()

    title = args.title
    message = args.message
    if args.test:
        title = "Alix — Connexion Établie ⚡"
        message = "Le module de notification proactive est opérationnel à l'établi !"

    notify_alix(title, message, priority=args.priority, play_sound=not args.no_sound)


if __name__ == "__main__":
    main()

