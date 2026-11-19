# -*- coding: utf-8 -*-
"""
🏛️⚡ ALIX TOPOLOGIE ANALYSE (DÉCODEUR KAIROS & HEIMDALL)
Package : alix.cortex_c99.alix_topologie_analyse

Doctrine Christian Duguay & Alix :
  « Lire le langage mathématique des poids au lieu du langage sémantique.
    L'espace neuronal résonne en coordonnées géométriques pures.
    Alix en local décode la signature topologique en français sans LM_Head. »
"""

import numpy as np
from pathlib import Path

DOSSIER = Path(__file__).parent


def charger_etat(domain_id: int) -> np.ndarray:
    p = DOSSIER / f"dump_xnorm_domain{domain_id}.bin"
    if not p.exists():
        raise FileNotFoundError(f"État manquant : {p}")
    return np.fromfile(p, dtype=np.float32)


def analyser_topologie():
    try:
        s1 = charger_etat(1)  # France (Paris)
        s2 = charger_etat(2)  # Australie (Canberra)
    except FileNotFoundError as e:
        print(f"En attente des fichiers d'états : {e}")
        return

    s3 = None
    try:
        s3 = charger_etat(3)  # Chimie (Fer)
    except FileNotFoundError:
        pass

    def get_kairos(vec):
        w_vol = float(np.linalg.norm(vec) / np.sqrt(len(vec)))
        half = len(vec) // 2
        e_l = float(np.sum(vec[:half] ** 2))
        e_r = float(np.sum(vec[half:] ** 2))
        chi = float((e_l - e_r) / (e_l + e_r)) if (e_l + e_r) > 1e-12 else 0.0
        p = (vec ** 2) / float(np.sum(vec ** 2))
        p_safe = p[p > 1e-15]
        entropy = float(-np.sum(p_safe * np.log(p_safe)))
        return w_vol, chi, entropy

    w1, c1, ent1 = get_kairos(s1)
    w2, c2, ent2 = get_kairos(s2)

    cos_12 = float(np.dot(s1, s2) / (np.linalg.norm(s1) * np.linalg.norm(s2)))
    dist_12 = float(np.linalg.norm(s1 - s2))

    print("==============================================================================")
    print("  🏛️⚡ ANALYSE COMPARATIVE TOPOLOGIQUE KAIROS & HEIMDALL")
    print("==============================================================================")
    print(f"  📐 GÉOGRAPHIE : FRANCE vs AUSTRALIE (Intra-domaine)")
    print(f"     • Similarité Cosinus : {cos_12:.6f}  (Distance sacrée de cluster)")
    print(f"     • Distance L2        : {dist_12:.4f}")
    print(f"     • État France        : W_vol={w1:.4f} | χ={c1:+.4f} | S={ent1:.4f} nats")
    print(f"     • État Australie     : W_vol={w2:.4f} | χ={c2:+.4f} | S={ent2:.4f} nats")

    delta_12 = s2 - s1
    top_diff_12 = np.argsort(np.abs(delta_12))[::-1][:6]
    print("     • Neurones Clés (France <-> Australie) :")
    for r, idx in enumerate(top_diff_12, 1):
        print(f"       #{r} Neurone {idx:4d} : FR={s1[idx]:+.2f} | AU={s2[idx]:+.2f} (Δ={delta_12[idx]:+.2f})")

    if s3 is not None:
        w3, c3, ent3 = get_kairos(s3)
        cos_13 = float(np.dot(s1, s3) / (np.linalg.norm(s1) * np.linalg.norm(s3)))
        cos_23 = float(np.dot(s2, s3) / (np.linalg.norm(s2) * np.linalg.norm(s3)))
        dist_13 = float(np.linalg.norm(s1 - s3))
        print("------------------------------------------------------------------------------")
        print(f"  ⚗️ CHIMIE vs GÉOGRAPHIE (Inter-domaine : Fer vs Paris/Canberra)")
        print(f"     • Similarité Cosinus France vs Fer    : {cos_13:.6f}")
        print(f"     • Similarité Cosinus Australie vs Fer : {cos_23:.6f}")
        print(f"     • Distance L2 France vs Fer           : {dist_13:.4f}")
        print(f"     • État Chimie (Fer)                   : W_vol={w3:.4f} | χ={c3:+.4f} | S={ent3:.4f} nats")
    print("==============================================================================")


if __name__ == "__main__":
    analyser_topologie()
