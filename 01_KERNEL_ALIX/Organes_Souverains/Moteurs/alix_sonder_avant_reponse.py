# -*- coding: utf-8 -*-
"""
================================================================================
     TRIPLE SONDE AVANT RÉPONSE — Présent × Mémoire × Actualité
================================================================================
Ordre :
  1. PRÉSENT   : lit Present/alix_present.json (sinon pulsation immédiate).
  2. MÉMOIRE   : alix_interroger_memoire.py "<sujet>"  (PSI-21, mémoire avant calcul)
  3. ACTUALITÉ : alix_sonde_actualite.py "<sujet>"     (le monde a bougé depuis ?)

Usage :
  python alix_sonder_avant_reponse.py "élections Québec Granby"
  python alix_sonder_avant_reponse.py "sujet" --sans-web
================================================================================
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MOTEURS = Path(__file__).resolve().parent
sys.path.insert(0, str(MOTEURS))
ETAT = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix\Present\alix_present.json")
PERIME_S = 180  # au-delà, le daemon est considéré mort -> pulsation directe


def present() -> dict:
    try:
        etat = json.loads(ETAT.read_text(encoding="utf-8"))
        age = (datetime.now().astimezone() - datetime.fromisoformat(etat["horodatage"])).total_seconds()
        etat["age_secondes"] = round(age)
        etat["daemon_vivant"] = age < PERIME_S
        if etat["daemon_vivant"]:
            return etat
    except Exception:
        pass
    import alix_sonde_present
    etat = alix_sonde_present.pulsation(garder=20, largeur=1280)
    etat["age_secondes"] = 0
    etat["daemon_vivant"] = False
    return etat


def main():
    p = argparse.ArgumentParser()
    p.add_argument("sujet")
    p.add_argument("--sans-web", action="store_true")
    p.add_argument("--jours", type=int, default=2)
    a = p.parse_args()

    e = present()
    print("🕰️ [1/3] PRÉSENT")
    print("=" * 74)
    print(f"   Maintenant      : {e['date_lisible']} ({e['horodatage']})")
    print(f"   Fenêtre active  : {e['fenetre_active']}")
    print(f"   Dernière capture: {e['derniere_capture']}")
    print(f"   Daemon          : {'🟢 vivant' if e['daemon_vivant'] else '🟡 absent (pulsation directe)'}")
    try:
        from alix_sonar_multimodal import AlixSonarMultimodal
        s = AlixSonarMultimodal()
        d_sonar = s.sonder_ecran_actuel(top_k=2)
        if d_sonar.get("statut") == "succes":
            print(f"   👁️ Sonar Écran   : {d_sonar['domaine_dominant']} ({d_sonar['score_dominant']:+.4f}) en {d_sonar['temps_encodage_ms']} ms")
        s.close()
    except Exception:
        pass

    try:
        spec_path = VAULT / "alix_speculation_live.json"
        if spec_path.exists():
            with open(spec_path, "r", encoding="utf-8") as f_spec:
                spec_data = json.load(f_spec)
                print(f"   🦅 Éclaireur K-SIL: Souverain {spec_data['anticipation']['souverain_prioritaire']} | mmap CPU {spec_data['performance_tri_puces']['pont_cpu_mmap_us']} µs | GPU {spec_data['performance_tri_puces']['rafale_gpu_ms']} ms")
    except Exception:
        pass

    print("\n🧠 [2/3] MÉMOIRE LOCALE", flush=True)
    subprocess.run([sys.executable, str(MOTEURS / "alix_interroger_memoire.py"), a.sujet])

    if not a.sans_web:
        print("\n🌐 [3/3] ACTUALITÉ DU MOMENT")
        import alix_sonde_actualite as act
        act.afficher(act.sonder(a.sujet, jours=a.jours))
        print("\n⚠️  Règle : si la mémoire contredit l'actualité, l'ACTUALITÉ datée l'emporte "
              "et la mémoire est marquée périmée.")


if __name__ == "__main__":
    main()

