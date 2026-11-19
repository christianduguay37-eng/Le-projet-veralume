import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Christian\Documents\Cerveau Alix").resolve()

# 1. Réparation automatique du BOM UTF-8 (U+FEFF)
bom_files = [
    ROOT / "alix_capability_dispatcher.py",
    ROOT / "_Archives_Exocerveau_Legacy_20261025" / "Racine_Python_Legacy" / "chat_loki_740m_dyade.py"
]

print("=== 1. RÉPARATION DES FICHIERS AVEC BOM (U+FEFF) ===")
for bf in bom_files:
    if bf.exists():
        raw = bf.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            bf.write_bytes(raw[3:])
            print(f"[RÉPARÉ] Caractère U+FEFF supprimé dans : {bf.relative_to(ROOT)}")
        else:
            print(f"[OK] Aucun BOM détecté dans : {bf.relative_to(ROOT)}")
    else:
        print(f"[NON TROUVÉ] {bf}")

# 2. Comparaison des paires de fichiers en doublon structurel
clusters_to_compare = {
    "Moteurs Déductifs (Causal vs Poseidon v10)": [
        "Organes_Souverains/Moteurs/alix_moteur_deductif_causal.py",
        "Organes_Souverains/Moteurs/alix_moteur_deductif_poseidon_v10.py",
    ],
    "Moteur Fractal (Racine vs Capacité)": [
        "veralume_core_engine.py",
        "Organes_Souverains/Capacites_Live/capacite_four_micro_ondes_deduction_fractale.py",
    ],
    "Organismes Vocaux (Fusion vs V4 vs Souverain Local)": [
        "Organes_Souverains/Capteurs/alix_vocal_organism_fusion.py",
        "Organes_Souverains/Capteurs/alix_vocal_organism_v4.py",
        "Organes_Souverains/Capteurs/alix_vocal_souverain_local.py",
    ],
    "Communication Telegram (Daemon vs Passerelle)": [
        "Organes_Souverains/Moteurs/alix_daemon_communication_distante.py",
        "Organes_Souverains/Moteurs/alix_passerelle_telegram.py",
    ],
    "Sondes Scientifiques (Turing vs Landauer)": [
        "Organes_Souverains/Moteurs/alix_sonde_auto_organisation_turing.py",
        "Organes_Souverains/Moteurs/alix_sonde_transversale_landauer.py",
    ],
    "Vision Argus (Synchrone RAM vs 24fps vs Daemon)": [
        "Organes_Souverains/Moteurs/alix_argus_synchrone_ram.py",
        "Organes_Souverains/Moteurs/alix_argus_vision_24fps.py",
        "Organes_Souverains/Moteurs/alix_daemon_argus.py",
    ],
    "Point d'entrée Racine (alix.py vs alix_engine.py)": [
        "alix.py",
        "alix_engine.py",
    ]
}

print("\n=== 2. COMPARAISON DES VERSIONS MAÎTRESSES ===")
for title, paths in clusters_to_compare.items():
    print(f"\n-> {title} :")
    for p_str in paths:
        p = ROOT / Path(p_str)
        if p.exists():
            stat = p.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            lines = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
            print(f"   [{mtime}] {lines:>5} lignes | {p_str}")
        else:
            print(f"   [ABSENT] {p_str}")
