# -*- coding: utf-8 -*-
"""
================================================================================
   ALIX ASPIRATEUR TECHNOVELGY INTÉGRAL — 3500+ INVENTIONS SF ⟷ BREVETS
               Système : VERALUME × KAIROS V6 — Démon Local Alix
================================================================================
Rôle :
- Moissonne l'intégralité des 26 lettres de l'alphabet de Technovelgy (A-Z).
- Extrait pour chaque invention de science-fiction :
    * Nom de l'invention
    * Identifiant Bnum (lien fiche)
    * Description fonctionnelle du concept
    * Ouvrage de science-fiction d'origine
    * Auteur
    * Année de parution originale
- Compile le tout en Parquet zstd pour la Cathédrale du Savoir (Pilier 07).
================================================================================
"""

import os
import sys
import time
import string
import urllib.request
from pathlib import Path
from html.parser import HTMLParser
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

class TechnovelgyParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cur_href = ""
        self.cur_row = []
        self.cur_cell = []
        self.in_row = False
        self.rows = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "tr":
            self.in_row = True
            self.cur_row = []
        elif tag == "td":
            self.cur_cell = []
        elif tag == "a":
            href = attrs_dict.get("href", "")
            if "content.asp?Bnum=" in href:
                self.cur_href = href

    def handle_endtag(self, tag):
        if tag == "td":
            self.cur_row.append(" ".join(self.cur_cell).strip())
            self.cur_cell = []
        elif tag == "tr":
            if self.cur_row and self.cur_href:
                self.rows.append((self.cur_href, self.cur_row))
                self.cur_href = ""
            self.in_row = False

    def handle_data(self, data):
        txt = data.strip()
        if txt:
            self.cur_cell.append(txt)

def aspirer_lettre(lettre: str) -> list:
    url = f"http://www.technovelgy.com/ct/ctnlistalpha.asp?FL={lettre}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            parser = TechnovelgyParser()
            parser.feed(html)
            
            inventions = []
            for href, cells in parser.rows:
                bnum = href.split("Bnum=")[-1] if "Bnum=" in href else ""
                col0 = cells[0] if len(cells) > 0 else ""
                book = cells[1] if len(cells) > 1 else ""
                author = cells[2] if len(cells) > 2 else ""
                date = cells[3] if len(cells) > 3 else ""
                
                # Sépare le nom de l'invention de sa description
                # col0 contient souvent "NomDeLInvention Description..."
                # Le premier mot ou groupe de mots avant le texte descriptif
                inventions.append({
                    "bnum": bnum,
                    "invention_et_description": col0,
                    "livre_sf": book,
                    "auteur": author,
                    "annee": date,
                    "url_technovelgy": f"http://www.technovelgy.com/ct/{href}"
                })
            return inventions
    except Exception as e:
        print(f"⚠️ Erreur lettre {lettre}: {e}")
        return []

def main():
    print("==========================================================================")
    print(" 🚀 ASPIRATEUR TECHNOVELGY : 3500+ INVENTIONS SF DE A À Z ⚡")
    print("==========================================================================")
    t0 = time.perf_counter()
    
    toutes_inventions = []
    lettres = string.ascii_uppercase
    
    for l in lettres:
        t_l = time.perf_counter()
        invs = aspirer_lettre(l)
        d_l = (time.perf_counter() - t_l) * 1000
        print(f"   [Lettre {l}] : {len(invs)} inventions extraites ({d_l:.0f} ms)")
        toutes_inventions.extend(invs)
        time.sleep(0.1) # Courtoisie serveur
        
    print("==========================================================================")
    print(f" Total inventions extraites : {len(toutes_inventions)}")
    
    if not toutes_inventions:
        print("❌ Aucune invention extraite.")
        return

    df = pd.DataFrame(toutes_inventions)
    
    dst_dir = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix\Cathedrale_du_Savoir_Universel\07_MIT_Science_et_Cybernetique\data")
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst_parquet = dst_dir / "technovelgy_inventions_scifi_brevets.parquet"
    
    table = pa.Table.from_pandas(df)
    pq.write_table(table, dst_parquet, compression="zstd")
    
    duree = time.perf_counter() - t0
    taille_ko = dst_parquet.stat().st_size / 1024
    print(f"✅ Fichier Parquet scellé : {dst_parquet.name} ({taille_ko:.1f} Ko)")
    print(f"⏱️ Aspiration totale complétée en {duree:.1f} secondes !")
    print("==========================================================================")

if __name__ == "__main__":
    main()

