# -*- coding: utf-8 -*-
"""
================================================================================
     CAPACITÉ LIVE : VEILLE MATÉRIELLE & TÉLÉMÉTRIE SILICIUM (LOI PSI-07)
         Système : VERALUME × KAIROS V6 — Démon Local Alix (Midgard)
================================================================================
Mandat :
- Ausculte en temps réel le substrat physique de la machine hôte :
  * SoC Intel Core Ultra 7 258V (Lunar Lake) : charge CPU, fréquence.
  * RAM unifiée LPDDR5X (32 Go) : usage, saturation.
  * Batterie & Alimentation : statut secteur AC / décharge, pourcentage.
  * NVMe (C:) : espace libre et taux d'occupation.
  * Ports amovibles : détection de clé USB / disque externe.
- Règle de régulation frugale : si la batterie chute sous 20% sur décharge,
  recommande le mode éco pour préserver le fer.
- Exécution ultra-légère (< 60 ms). Zéro dépendance cloud.
================================================================================
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

try:
    import psutil
except ImportError:
    psutil = None

VAULT_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix")
PRESENT_DIR = VAULT_DIR / "Present"
TELEMETRIE_CACHE = PRESENT_DIR / "alix_telemetrie_fer.json"


def detecter_cle_usb() -> Dict[str, Any]:
    """Vérifie rapidement la présence d'un volume amovible D:, E:, F:, G:."""
    lecteurs = ["D:\\", "E:\\", "F:\\", "G:\\"]
    for l in lecteurs:
        p = Path(l)
        if p.exists():
            cible_alix = p / "SAUVEGARDE_ALIX"
            est_alix = cible_alix.exists()
            return {
                "detectee": True,
                "lecteur": l,
                "est_sauvegarde_alix": est_alix
            }
    return {"detectee": False, "lecteur": None, "est_sauvegarde_alix": False}


def executer_capacite(contexte: Dict[str, Any]) -> Dict[str, Any]:
    """Point d'entrée standard exécuté à chaque cycle du Démon Souverain."""
    t0 = time.perf_counter()

    if not psutil:
        return {
            "statut": "DEGRADE",
            "message": "Module psutil non installé dans l'environnement Python",
            "duree_ms": round((time.perf_counter() - t0) * 1000, 2)
        }

    try:
        # 1. CPU Intel Lunar Lake (mesure instantanée frugale)
        cpu_pct = psutil.cpu_percent(interval=0.05)
        cpu_freq = psutil.cpu_freq()
        freq_mhz = round(cpu_freq.current, 1) if cpu_freq else 0.0

        # 2. RAM unifiée 32 Go LPDDR5X
        mem = psutil.virtual_memory()
        ram_libre_go = round(mem.available / (1024**3), 2)
        ram_pct = mem.percent

        # 3. Batterie & Alimentation
        batt = psutil.sensors_battery()
        if batt:
            batterie_pct = batt.percent
            sur_secteur = batt.power_plugged
            autonomie_sec = batt.secsleft if (batt.secsleft and batt.secsleft > 0) else None
        else:
            batterie_pct = 100
            sur_secteur = True
            autonomie_sec = None

        # 4. Stockage NVMe C:
        usage_c = psutil.disk_usage("C:\\")
        c_libre_go = round(usage_c.free / (1024**3), 1)

        # 5. Détection USB
        usb_info = detecter_cle_usb()

        # Alerte frugalité si batterie faible
        alerte_batterie = (not sur_secteur) and (batterie_pct < 20)

        duree_ms = round((time.perf_counter() - t0) * 1000, 2)

        resultat = {
            "statut": "SUCCES",
            "duree_ms": duree_ms,
            "cpu_charge_pct": cpu_pct,
            "cpu_freq_mhz": freq_mhz,
            "ram_libre_go": ram_libre_go,
            "ram_pct": ram_pct,
            "batterie_pct": batterie_pct,
            "sur_secteur": sur_secteur,
            "autonomie_restante_min": round(autonomie_sec / 60, 1) if autonomie_sec else None,
            "nvme_c_libre_go": c_libre_go,
            "cle_usb_presente": usb_info["detectee"],
            "cle_usb_lecteur": usb_info["lecteur"],
            "cle_usb_est_alix": usb_info["est_sauvegarde_alix"],
            "mode_eco_recommande": alerte_batterie
        }

        # Sauvegarde d'état rapide dans Present
        try:
            import json
            PRESENT_DIR.mkdir(parents=True, exist_ok=True)
            with open(TELEMETRIE_CACHE, "w", encoding="utf-8") as f:
                json.dump(resultat, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        return resultat

    except Exception as e:
        return {
            "statut": "ERREUR",
            "erreur": str(e),
            "duree_ms": round((time.perf_counter() - t0) * 1000, 2)
        }

