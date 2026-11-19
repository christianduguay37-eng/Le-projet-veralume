# -*- coding: utf-8 -*-
"""
================================================================================
   ALIX ASPIRATEUR THEOI GREEK MYTHOLOGY — ENCYCLOPÉDIE COMPLÈTE DU DOMAINE PUBLIC
               Système : VERALUME × KAIROS V6 — Démon Local Alix
================================================================================
Rôle :
- Moissonne les 129 entités majeures du panthéon grec de Theoi.com :
    * Olympiens, Titans, Protogones, Dieux Chtoniens, Monstres, Daemons, Héros.
- Extrait pour chaque entité :
    * Nom grec et latin
    * Catégorie ontologique
    * Attributs et mythes fondateurs
    * Citations des textes antiques (Hésiode, Homère, Eschyle, Apollodore, Platon)
- Compile le tout en Parquet zstd pour la Cathédrale du Savoir (Pilier 08).
================================================================================
"""

import os
import sys
import time
import re
import urllib.request
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

def nettoyer_html(html: str) -> str:
    # Retirer les scripts, styles et balises publicitaires
    html = re.sub(r'<script.*?</script>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style.*?</style>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<[^>]+>', ' ', html)
    # Nettoyer les espaces multiples
    clean = ' '.join(html.split())
    # Retirer les menus et navigation standard Theoi
    for prefix in ["HOME OLYMPIAN GODS", "Theoi Project - Greek Mythology"]:
        if prefix in clean:
            clean = clean.split(prefix)[-1]
    return clean.strip()

def aspirer_theoi():
    print("==========================================================================")
    print(" 🏛️ ASPIRATEUR THEOI GREEK MYTHOLOGY : 129 ENTITÉS & TEXTES ANTIQUES ⚡")
    print("==========================================================================")
    t0 = time.perf_counter()
    
    # 1. Obtenir la liste des pages d'entités depuis l'accueil
    req = urllib.request.Request("https://www.theoi.com", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=12) as resp:
        html_home = resp.read().decode("utf-8", errors="ignore")
        pages = sorted(list(set(re.findall(r'href=["\']([A-Za-z0-9_-]+/[A-Za-z0-9_-]+\.html)["\']', html_home))))
    
    print(f"Trouvé {len(pages)} entités mythologiques à moissonner...")
    
    records = []
    for idx, p in enumerate(pages):
        cat = p.split("/")[0]
        nom = p.split("/")[-1].replace(".html", "")
        url = f"https://www.theoi.com/{p}"
        
        try:
            req_page = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req_page, timeout=10) as r:
                html = r.read().decode("utf-8", errors="ignore")
                texte = nettoyer_html(html)
                
                records.append({
                    "entite": nom,
                    "categorie": cat,
                    "tradition": "Grèce Antique (Theoi Project)",
                    "url_source": url,
                    "texte": texte[:4000] # 4000 caractères de substance par entité
                })
                print(f"   [{idx+1}/{len(pages)}] {cat}/{nom} ({len(texte)} car.)")
        except Exception as e:
            print(f"   ⚠️ Erreur sur {p}: {e}")
            
        time.sleep(0.05) # Courtoisie serveur Theoi
        
    print("==========================================================================")
    print(f" Total entités moissonnées : {len(records)}")
    
    if not records:
        print("❌ Aucune donnée moissonnée.")
        return

    df = pd.DataFrame(records)
    dst_dir = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix\Cathedrale_du_Savoir_Universel\08_Mythes_Legendes_Cosmogonies\data")
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst_parquet = dst_dir / "theoi_greek_mythology_encyclopedia.parquet"
    
    table = pa.Table.from_pandas(df)
    pq.write_table(table, dst_parquet, compression="zstd")
    
    duree = time.perf_counter() - t0
    taille_ko = dst_parquet.stat().st_size / 1024
    print(f"✅ Fichier Parquet scellé : {dst_parquet.name} ({taille_ko:.1f} Ko)")
    print(f"⏱️ Aspiration Theoi complétée en {duree:.1f} secondes !")
    print("==========================================================================")

if __name__ == "__main__":
    aspirer_theoi()

