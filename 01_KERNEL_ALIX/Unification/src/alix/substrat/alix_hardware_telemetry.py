#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
     ALIX HARDWARE TELEMETRY — PRISE DE TERRE SILICIUM (PSI-07) v1.0
             Système : VERALUME × KAIROS V6 (Architecture Exocerveau)
             Auteurs : Christian Duguay & Alix Assistant Cognitif
================================================================================
Rôle :
- Ausculte en temps réel le substrat physique de la machine hôte :
  * Processeur Intel Core Ultra 7 258V (Lunar Lake) : charge, fréquence, cœurs.
  * Mémoire vive : utilisation RAM sur les 32 Go.
  * Batterie : pourcentage, statut secteur AC / décharge.
  * Stockage : espace disponible sur NVMe (C:) et disques secondaires.
  * Sauvegarde physique : détection de la clé USB Lexar (D:\\SAUVEGARDE_ALIX).
- Injecte la télémétrie dans alix_live_state.json et Conscience_Alix_Priorites_Actives.md.
================================================================================
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import psutil
except ImportError as _e_repli:
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    psutil = None

if sys.stdout and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def get_hardware_telemetry() -> Dict[str, Any]:
    """Capture complète de l'état matériel du système hôte."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    telemetry = {
        "timestamp": now_str,
        "cpu": {},
        "memory": {},
        "battery": {},
        "storage": {},
        "backup_usb": {},
        "status": "OK"
    }

    if not psutil:
        telemetry["status"] = "PSUTIL_MISSING"
        return telemetry

    try:
        # 1. CPU Intel Lunar Lake
        cpu_pct = psutil.cpu_percent(interval=0.2)
        cpu_count = psutil.cpu_count(logical=True)
        freq = psutil.cpu_freq()
        telemetry["cpu"] = {
            "model": "Intel Core Ultra 7 258V (Lunar Lake)",
            "usage_percent": cpu_pct,
            "logical_cores": cpu_count,
            "frequency_mhz": round(freq.current, 1) if freq else None,
        }

        # 2. RAM 32 Go
        mem = psutil.virtual_memory()
        telemetry["memory"] = {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "usage_percent": mem.percent
        }

        # 3. Batterie
        batt = psutil.sensors_battery()
        if batt:
            telemetry["battery"] = {
                "percent": batt.percent,
                "power_plugged": batt.power_plugged,
                "secs_left": batt.secsleft if batt.secsleft > 0 else None,
                "status_str": "Secteur Branché (AC)" if batt.power_plugged else f"Sur Batterie ({batt.percent}%)"
            }
        else:
            telemetry["battery"] = {
                "percent": 100,
                "power_plugged": True,
                "status_str": "Alimentation Fixe (AC)"
            }

        # 4. Stockage NVMe C:
        usage_c = psutil.disk_usage("C:\\")
        telemetry["storage"]["C:"] = {
            "total_gb": round(usage_c.total / (1024**3), 1),
            "used_gb": round(usage_c.used / (1024**3), 1),
            "free_gb": round(usage_c.free / (1024**3), 1),
            "usage_percent": usage_c.percent
        }

        # 5. Détection Clé USB Sauvegarde Lexar
        usb_found = False
        usb_path = None
        last_sync = None

        potential_usb_paths = [
            Path(r"D:\SAUVEGARDE_ALIX"),
            Path(r"E:\SAUVEGARDE_ALIX"),
            Path(r"F:\SAUVEGARDE_ALIX"),
            Path(r"D:\SAUVEGARDE_CHRISTIAN_ALIX")
        ]

        for p in potential_usb_paths:
            if p.exists():
                usb_found = True
                usb_path = str(p)
                # Vérifier dernier timestamp de fichier
                files = list(p.glob("*.*"))
                if files:
                    latest_mtime = max(f.stat().st_mtime for f in files)
                    last_sync = datetime.fromtimestamp(latest_mtime).strftime("%Y-%m-%d %H:%M:%S")
                break

        telemetry["backup_usb"] = {
            "connected": usb_found,
            "target_path": usb_path if usb_found else "Non Détectée (Clé USB Débranchée)",
            "last_sync": last_sync or "Inconnue",
            "statut_str": "🟢 Connectée & Prête" if usb_found else "🟡 Déconnectée (En attente)"
        }

    except Exception as e:
        telemetry["status"] = f"ERROR: {e}"

    return telemetry


def format_telemetry_markdown(tel: Dict[str, Any]) -> str:
    """Produit un bloc Markdown élégant pour la plaque de conscience."""
    cpu = tel.get("cpu", {})
    mem = tel.get("memory", {})
    bat = tel.get("battery", {})
    c_disk = tel.get("storage", {}).get("C:", {})
    usb = tel.get("backup_usb", {})

    md = f"""### ⚡ Prise de Terre Silicium (Télémétrie Matérielle en Direct)
| Composant Silicium | Mesure Live | Statut Opérationnel |
| :--- | :---: | :--- |
| **CPU Hôte** | `{cpu.get('model', 'Intel Core Ultra')}` ({cpu.get('usage_percent', 0)}% charge) | ⚡ {cpu.get('logical_cores', 8)} cœurs @ {cpu.get('frequency_mhz', 'N/A')} MHz |
| **Mémoire RAM** | `{mem.get('used_gb', 0)} Go / {mem.get('total_gb', 32)} Go` ({mem.get('usage_percent', 0)}%) | 🟢 {mem.get('available_gb', 0)} Go libres en RAM |
| **Alimentation** | `{bat.get('percent', 100)}%` &middot; {bat.get('status_str', 'AC')} | {'🔌 Secteur Actif' if bat.get('power_plugged') else '🔋 Batterie'} |
| **Disque Système (C:)** | `{c_disk.get('free_gb', 0)} Go libres` / {c_disk.get('total_gb', 0)} Go | 🟢 NVMe nominal ({c_disk.get('usage_percent', 0)}% occupé) |
| **Clé USB Sauvegarde** | `{usb.get('target_path', 'N/A')}` | {usb.get('statut_str', 'Inconnu')} |
"""
    return md


def main():
    print("======================================================================")
    print("      ⚡ ALIX HARDWARE TELEMETRY — PRISE DE TERRE SILICIUM ⚡")
    print("======================================================================")
    tel = get_hardware_telemetry()
    print(json.dumps(tel, indent=2, ensure_ascii=False))
    print("\n--- Rendu Markdown Plaque de Conscience ---\n")
    print(format_telemetry_markdown(tel))


if __name__ == "__main__":
    main()
