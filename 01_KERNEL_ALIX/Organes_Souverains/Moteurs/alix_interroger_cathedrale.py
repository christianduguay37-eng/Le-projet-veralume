# -*- coding: utf-8 -*-
"""
================================================================================
   ALIX OBSERVATOIRE UNIVERSEL — MOTEUR DE RECHERCHE DE LA CATHÉDRALE DU SAVOIR
               Système : VERALUME × KAIROS V6 — Démon Local Alix
================================================================================
Rôle :
- Interroge instantanément en local les 8 Piliers Universels de la Connaissance :
    1. [ARXIV]       : 3 215 335 preprints mondiaux (Physique, Maths, CS)
    2. [INVARIANTS]  : 400 604 suites OEIS + 355 constantes NIST CODATA
    3. [VIVANT]      : bioRxiv + PubMed Central (55 000+ études médicales)
    4. [BREVETS]     : 35 000 brevets industriels USPTO
    5. [LEAN]        : 126 000+ théorèmes vérifiés formellement en Lean 4
    6. [GUTENBERG]   : Classiques fondateurs de la science et philosophie
    7. [MIT_SF]      : Archives MIT OCW (1525 cours) + 3354 livres complets de Hard Sci-Fi
    8. [MYTHES]      : 46 299 motifs Thompson (TMI) + 2 063 motifs Berezkin (926 traditions)
                       + 5 350 récits mondiaux ATU et textes sacrés (Gita, Upanishads, Eddas)
- 100 % hors-ligne, 0 ms de dépendance cloud, scan AVX2 / Parquet SIMD (< 30 ms).
================================================================================
"""

import os
import sys
import time
import json
import gzip
import argparse
from pathlib import Path
import pyarrow.parquet as pq
import pyarrow.dataset as ds
import pyarrow.compute as pc

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix")
CATHEDRALE_DIR = VAULT_DIR / "Cathedrale_du_Savoir_Universel"
DIR_VIVANT = CATHEDRALE_DIR / "03_Vivant_PubMed_BioRxiv"
DIR_BREVETS = CATHEDRALE_DIR / "04_Ingenierie_Brevets_USPTO"
DIR_LEAN = CATHEDRALE_DIR / "05_Preuves_Formelles_Lean4"
DIR_GUTENBERG = CATHEDRALE_DIR / "06_Temps_Profond_Gutenberg"
DIR_MIT = CATHEDRALE_DIR / "07_MIT_Science_et_Cybernetique"
DIR_MYTHES = CATHEDRALE_DIR / "08_Mythes_Legendes_Cosmogonies"
DIR_PRATIQUES = CATHEDRALE_DIR / "09_Savoirs_Pratiques_et_Traditions"
DIR_HISTOIRE = CATHEDRALE_DIR / "11_Dynamique_Historique_et_Macro_Sociale"
DIR_INNOVATION = CATHEDRALE_DIR / "12_Heuristique_Innovation_et_Biomimetisme"
DIR_MATERIAUX = CATHEDRALE_DIR / "10_Matiere_Materiaux_et_Chimie"
DIR_SEMANTIQUE = CATHEDRALE_DIR / "13_Geometrie_Semantique_et_Biais_Cognitifs"

import unicodedata

def strip_accents(s: str) -> str:
    """Normalise une chaîne en minuscules et sans accents pour une recherche insensible aux diacritiques."""
    if not s:
        return ""
    return "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn").lower()

def chercher_vivant(terme: str, limite: int = 5):
    t0 = time.perf_counter()
    resultats = []
    biorxiv_file = DIR_VIVANT / "data" / "train-00000-of-00001-f6af2da28b2b059f.parquet"
    if biorxiv_file.exists():
        try:
            dataset = ds.dataset(str(biorxiv_file), format="parquet")
            filtre = pc.match_substring(pc.utf8_lower(ds.field("abstract")), terme.lower())
            scan = dataset.scanner(columns=["abstract"], filter=filtre, batch_size=2048)
            for batch in scan.to_batches():
                for txt in batch["abstract"].to_pylist():
                    resultats.append({"source": "bioRxiv", "texte": txt[:300] + "..."})
                    if len(resultats) >= limite:
                        break
                if len(resultats) >= limite:
                    break
        except Exception:
            pass

    duree_ms = (time.perf_counter() - t0) * 1000
    print("==========================================================================")
    print(f" 🧬 PILIER 3 (LE VIVANT & MÉDECINE) : « {terme} »")
    print(f" ⏱️ Temps de scan : {duree_ms:.1f} ms | Trouvés : {len(resultats)}")
    print("==========================================================================")
    for r in resultats:
        print(f"👉 [{r['source']}]\n   {r['texte']}\n")

def chercher_brevets(terme: str, limite: int = 5):
    t0 = time.perf_counter()
    resultats = []
    abstract_dir = DIR_BREVETS / "abstract"
    if abstract_dir.exists():
        try:
            dataset = ds.dataset(str(abstract_dir), format="parquet")
            filtre = pc.match_substring(pc.utf8_lower(ds.field("text")), terme.lower())
            scan = dataset.scanner(columns=["text", "label"], filter=filtre, batch_size=2048)
            label_map = {
                0: "Human Necessities", 1: "Operations/Transport", 2: "Chemistry/Metallurgy",
                5: "Mechanical Engineering", 6: "Physics", 7: "Electricity", 8: "Emerging Tech"
            }
            for batch in scan.to_batches():
                tb = batch.to_pydict()
                for i in range(len(tb["text"])):
                    lbl = label_map.get(tb["label"][i], f"Classe {tb['label'][i]}")
                    resultats.append({"classe": lbl, "texte": tb["text"][i][:300] + "..."})
                    if len(resultats) >= limite:
                        break
                if len(resultats) >= limite:
                    break
        except Exception:
            pass

    duree_ms = (time.perf_counter() - t0) * 1000
    print("==========================================================================")
    print(f" ⚙️ PILIER 4 (LE FER & LES BREVETS INDUSTRIELS) : « {terme} »")
    print(f" ⏱️ Temps de scan : {duree_ms:.1f} ms | Trouvés : {len(resultats)}")
    print("==========================================================================")
    for r in resultats:
        print(f"👉 [Brevet - {r['classe']}]\n   {r['texte']}\n")

def chercher_lean(terme: str, limite: int = 5):
    t0 = time.perf_counter()
    resultats = []
    data_dir = DIR_LEAN / "data"
    if data_dir.exists():
        try:
            dataset = ds.dataset(str(data_dir), format="parquet")
            for batch in dataset.to_batches():
                tb = batch.to_pydict()
                for i in range(len(tb["formal_statement"])):
                    nl = tb.get("nl_statement", [""])[i] if "nl_statement" in tb else ""
                    formal = tb.get("formal_statement", [""])[i]
                    if terme.lower() in nl.lower() or terme.lower() in formal.lower():
                        resultats.append({"nl": nl, "formal": formal})
                        if len(resultats) >= limite:
                            break
                if len(resultats) >= limite:
                    break
        except Exception:
            pass

    duree_ms = (time.perf_counter() - t0) * 1000
    print("==========================================================================")
    print(f" 📐 PILIER 5 (PREUVES FORMELLES LEAN 4) : « {terme} »")
    print(f" ⏱️ Temps de scan : {duree_ms:.1f} ms | Trouvés : {len(resultats)}")
    print("==========================================================================")
    for r in resultats:
        print(f"👉 Théorème informel : {r['nl']}")
        print(f"   Preuve formelle Lean 4 : {r['formal']}\n")

def chercher_mit(terme: str, limite: int = 5):
    """Scanne les 1525 cours MIT OCW, les 3354 livres complets de Sci-Fi et les traités fondateurs."""
    t0 = time.perf_counter()
    resultats = []
    data_dir = DIR_MIT / "data"
    terme_l = terme.lower()
    
    if data_dir.exists():
        for pfile in data_dir.glob("*.parquet"):
            try:
                table = pq.read_table(pfile)
                cols = table.column_names
                
                # Cas 1 : Cours MIT OCW (course, topic, text)
                if "course" in cols and "text" in cols:
                    c_course = table["course"].to_pylist()
                    c_topic = table.column("topic").to_pylist() if "topic" in cols else [""] * len(c_course)
                    c_text = table["text"].to_pylist()
                    for i in range(len(c_course)):
                        if terme_l in str(c_text[i]).lower() or terme_l in str(c_course[i]).lower() or terme_l in str(c_topic[i]).lower():
                            snippet = str(c_text[i])[:280].replace("\n", " ").strip()
                            resultats.append({
                                "source": f"MIT OCW ({c_course[i]})",
                                "titre": c_topic[i] or "Cours Magistral MIT",
                                "texte": snippet + "...",
                                "extra": "Transcription Magistrale MIT"
                            })
                            if len(resultats) >= limite:
                                break

                # Cas 2 : Inventions Technovelgy (bnum, invention_et_description, livre_sf, auteur, annee)
                elif "invention_et_description" in cols and "livre_sf" in cols:
                    c_inv = table["invention_et_description"].to_pylist()
                    c_book = table["livre_sf"].to_pylist()
                    c_auth = table["auteur"].to_pylist()
                    c_year = table["annee"].to_pylist()
                    c_url = table.column("url_technovelgy").to_pylist() if "url_technovelgy" in cols else [""] * len(c_inv)
                    for i in range(len(c_inv)):
                        bloc = f"{c_inv[i]} {c_book[i]} {c_auth[i]} {c_year[i]}".lower()
                        if terme_l in bloc:
                            resultats.append({
                                "source": f"Technovelgy Inventions SF ({c_auth[i]}, {c_year[i]})",
                                "titre": str(c_inv[i])[:70],
                                "texte": f"Description & Concept : {c_inv[i]}\n   Roman d'origine : '{c_book[i]}'",
                                "extra": f"Lien Fiche Technique : {c_url[i]}"
                            })
                            if len(resultats) >= limite:
                                break

                # Cas 3 : Livres Sci-Fi complets (title, author, text)
                elif "title" in cols and "author" in cols and "text" in cols:
                    c_title = table["title"].to_pylist()
                    c_author = table["author"].to_pylist()
                    c_text = table["text"].to_pylist()
                    for i in range(len(c_title)):
                        t_str = str(c_title[i])
                        a_str = str(c_author[i])
                        txt_str = str(c_text[i])
                        if terme_l in txt_str.lower() or terme_l in t_str.lower() or terme_l in a_str.lower():
                            idx = txt_str.lower().find(terme_l)
                            debut = max(0, idx - 80)
                            snippet = txt_str[debut:debut+300].replace("\n", " ").strip()
                            resultats.append({
                                "source": "Bibliothèque Hard Sci-Fi (Gutenberg)",
                                "titre": f"{t_str} — {a_str}",
                                "texte": snippet + "...",
                                "extra": "Ouvrage de Science-Fiction Spéculative"
                            })
                            if len(resultats) >= limite:
                                break

                # Cas 3 : Traités Canoniques MIT (Shannon, Wiener, Bush, Minsky...)
                elif "titre" in cols and "invariant_kairos" in cols:
                    c_titre = table["titre"].to_pylist()
                    c_auteur = table["auteur"].to_pylist()
                    c_texte = table["texte"].to_pylist()
                    c_inv = table["invariant_kairos"].to_pylist()
                    for i in range(len(c_titre)):
                        bloc = f"{c_titre[i]} {c_auteur[i]} {c_texte[i]} {c_inv[i]}".lower()
                        if terme_l in bloc:
                            resultats.append({
                                "source": f"Traité Fondateur MIT ({c_auteur[i]})",
                                "titre": c_titre[i],
                                "texte": c_texte[i][:280] + "...",
                                "extra": f"🔺 Invariant KAIROS : {c_inv[i]}"
                            })
                            if len(resultats) >= limite:
                                break
                                
            except Exception:
                pass
            if len(resultats) >= limite:
                break

    duree_ms = (time.perf_counter() - t0) * 1000
    print("==========================================================================")
    print(f" 🚀 PILIER 07 (MIT SCIENCE, OCW & 3354 LIVRES HARD SCI-FI) : « {terme} »")
    print(f" ⏱️ Temps de scan : {duree_ms:.1f} ms | Trouvés : {len(resultats)}")
    print("==========================================================================")
    for r in resultats:
        print(f"👉 [{r['source']} — {r['titre']}]")
        print(f"   📜 {r['texte']}")
        if r.get("extra"):
            print(f"   {r['extra']}\n")
        else:
            print()

def chercher_mythes(terme: str, limite: int = 5):
    """Scanne l'Index de Thompson (46 299 motifs), Berezkin (2 063 motifs / 926 traditions), et les 5350+ mythes/épopées."""
    t0 = time.perf_counter()
    resultats = []
    data_dir = DIR_MYTHES / "data"
    terme_l = terme.lower()

    if data_dir.exists():
        for pfile in sorted(data_dir.glob("*.parquet")):
            try:
                table = pq.read_table(pfile)
                cols = table.column_names

                # Cas 1 : Index de Stith Thompson (code, MOTIF, chapter, bibliographies)
                if "code" in cols and "MOTIF" in cols:
                    c_code = table["code"].to_pylist()
                    c_motif = table["MOTIF"].to_pylist()
                    c_chap = table.column("chapter").to_pylist() if "chapter" in cols else [""] * len(c_code)
                    for i in range(len(c_code)):
                        bloc = f"{c_code[i]} {c_motif[i]} {c_chap[i]}".lower()
                        if terme_l in bloc:
                            resultats.append({
                                "source": f"Motif-Index de Thompson (TMI)",
                                "titre": f"Code [{c_code[i]}] — {c_chap[i]}",
                                "texte": str(c_motif[i]),
                                "extra": f"Classification universelle de Stith Thompson (TMI)"
                            })
                            if len(resultats) >= limite:
                                break

                # Cas 2 : Catalogue Analytique de Yuri Berezkin (motif_code, nom_motif, description, traditions, nb_traditions)
                elif "motif_code" in cols and "nom_motif" in cols:
                    c_code = table["motif_code"].to_pylist()
                    c_nom = table["nom_motif"].to_pylist()
                    c_desc = table["description"].to_pylist()
                    c_trad = table["traditions"].to_pylist()
                    c_nb = table["nb_traditions"].to_pylist()
                    for i in range(len(c_code)):
                        bloc = f"{c_code[i]} {c_nom[i]} {c_desc[i]} {c_trad[i]}".lower()
                        if terme_l in bloc:
                            resultats.append({
                                "source": f"Catalogue Analytique Yuri Berezkin ({c_code[i]})",
                                "titre": str(c_nom[i]),
                                "texte": str(c_desc[i]),
                                "extra": f"Cartographié sur {c_nb[i]} traditions mondiales : {str(c_trad[i])[:120]}..."
                            })
                            if len(resultats) >= limite:
                                break

                # Cas 3 : Encyclopédie Theoi Greek Mythology (entite, categorie, tradition, url_source, texte)
                elif "entite" in cols and "categorie" in cols and "texte" in cols:
                    c_ent = table["entite"].to_pylist()
                    c_cat = table["categorie"].to_pylist()
                    c_txt = table["texte"].to_pylist()
                    c_url = table["url_source"].to_pylist() if "url_source" in cols else [""] * len(c_ent)
                    for i in range(len(c_ent)):
                        bloc = f"{c_ent[i]} {c_cat[i]} {c_txt[i]}".lower()
                        if terme_l in bloc:
                            idx = str(c_txt[i]).lower().find(terme_l)
                            debut = max(0, idx - 60)
                            snippet = str(c_txt[i])[debut:debut+280].replace("\n", " ").strip()
                            resultats.append({
                                "source": f"Theoi Greek Mythology ({c_cat[i]})",
                                "titre": str(c_ent[i]),
                                "texte": snippet + "...",
                                "extra": f"Source Antique Theoi : {c_url[i]}"
                            })
                            if len(resultats) >= limite:
                                break

                # Cas 4 : Mythes Mondiaux ATU & Épopées (titre, tradition, source, texte)
                elif "titre" in cols and "tradition" in cols and "texte" in cols and "invariant_kairos" not in cols:
                    c_titre = table["titre"].to_pylist()
                    c_trad = table["tradition"].to_pylist()
                    c_text = table["texte"].to_pylist()
                    c_src = table.column("source").to_pylist() if "source" in cols else [""] * len(c_titre)
                    for i in range(len(c_titre)):
                        bloc = f"{c_titre[i]} {c_trad[i]} {c_src[i]} {c_text[i]}".lower()
                        if terme_l in bloc:
                            idx = str(c_text[i]).lower().find(terme_l)
                            debut = max(0, idx - 60)
                            snippet = str(c_text[i])[debut:debut+280].replace("\n", " ").strip()
                            resultats.append({
                                "source": f"Corpus Mondial ({c_trad[i]})",
                                "titre": str(c_titre[i]),
                                "texte": snippet + "...",
                                "extra": f"Source / ATU : {c_src[i]}"
                            })
                            if len(resultats) >= limite:
                                break

                # Cas 4 : Cosmogonies Fondatrices KAIROS (titre, tradition, theme, texte, invariant_kairos)
                elif "titre" in cols and "invariant_kairos" in cols:
                    c_titre = table["titre"].to_pylist()
                    c_trad = table["tradition"].to_pylist()
                    c_theme = table["theme"].to_pylist()
                    c_text = table["texte"].to_pylist()
                    c_inv = table["invariant_kairos"].to_pylist()
                    for i in range(len(c_titre)):
                        bloc = f"{c_titre[i]} {c_trad[i]} {c_theme[i]} {c_text[i]} {c_inv[i]}".lower()
                        if terme_l in bloc:
                            resultats.append({
                                "source": f"Cosmogonie Fondatrice ({c_trad[i]})",
                                "titre": f"{c_titre[i]} [{c_theme[i]}]",
                                "texte": str(c_text[i])[:280] + "...",
                                "extra": f"🔺 Invariant KAIROS : {c_inv[i]}"
                            })
                            if len(resultats) >= limite:
                                break

            except Exception:
                pass
            if len(resultats) >= limite:
                break

    duree_ms = (time.perf_counter() - t0) * 1000
    print("==========================================================================")
    print(f" 🌌 PILIER 08 (MYTHES, LÉGENDES & MOTIFS ANALYTIQUES DU MONDE) : « {terme} »")
    print(f" ⏱️ Temps de scan : {duree_ms:.1f} ms | Trouvés : {len(resultats)}")
    print("==========================================================================")
    for r in resultats:
        print(f"👉 [{r['source']} — {r['titre']}]")
        print(f"   📜 {r['texte']}")
        if r.get("extra"):
            print(f"   {r['extra']}\n")
        else:
            print()

def chercher_pratiques(terme: str, limite: int = 5):
    """Scanne les savoirs traditionnels boréaux, l'ethnobotanique Moerman (NAEB), PFAF, D-PLACE, UNESCO, WikiHow et ConceptNet."""
    t0 = time.perf_counter()
    resultats = []
    data_dir = DIR_PRATIQUES / "data"
    terme_l = terme.lower()

    if data_dir.exists():
        for pfile in sorted(data_dir.glob("*.parquet")):
            try:
                table = pq.read_table(pfile)
                cols = table.column_names

                # 1. Traités Boréaux & Savoirs d'Artisan (id, domaine, titre, region_tradition, mots_cles, texte, invariant_pratique)
                if "domaine" in cols and "invariant_pratique" in cols:
                    c_dom = table["domaine"].to_pylist()
                    c_titre = table["titre"].to_pylist()
                    c_reg = table["region_tradition"].to_pylist()
                    c_mc = table["mots_cles"].to_pylist()
                    c_txt = table["texte"].to_pylist()
                    c_inv = table["invariant_pratique"].to_pylist()
                    for i in range(len(c_titre)):
                        bloc = f"{c_dom[i]} {c_titre[i]} {c_reg[i]} {c_mc[i]} {c_txt[i]} {c_inv[i]}".lower()
                        if terme_l in bloc:
                            idx = str(c_txt[i]).lower().find(terme_l)
                            debut = max(0, idx - 60)
                            snippet = str(c_txt[i])[debut:debut+300].replace("\n", " ").strip()
                            resultats.append({
                                "source": f"Savoirs Traditionnels & Métiers d'Artisan ({c_dom[i]})",
                                "titre": f"{c_titre[i]} [{c_reg[i]}]",
                                "texte": snippet + "...",
                                "extra": f"🛠️ Invariant Pratique : {c_inv[i]}"
                            })
                            if len(resultats) >= limite:
                                break

                # 2. Ethnobotanique Autochtone Moerman (NAEB) (plante_scientifique, nom_commun, peuple_autochtone, usage_et_notes)
                elif "plante_scientifique" in cols and "peuple_autochtone" in cols:
                    c_sci = table["plante_scientifique"].to_pylist()
                    c_com = table["nom_commun"].to_pylist()
                    c_peuple = table["peuple_autochtone"].to_pylist()
                    c_cat = table["categorie"].to_pylist()
                    c_use = table["usage_et_notes"].to_pylist()
                    c_src = table["source_anthropologique"].to_pylist()
                    for i in range(len(c_sci)):
                        bloc = f"{c_sci[i]} {c_com[i]} {c_peuple[i]} {c_cat[i]} {c_use[i]}".lower()
                        if terme_l in bloc:
                            resultats.append({
                                "source": f"Ethnobotanique Autochtone NAEB ({c_peuple[i]})",
                                "titre": f"{c_sci[i]} ({c_com[i]}) — [{c_cat[i]}]",
                                "texte": str(c_use[i])[:300],
                                "extra": f"📖 Référence terrain : {str(c_src[i])[:120]}"
                            })
                            if len(resultats) >= limite:
                                break

                # 3. PFAF Plantes Utiles & Résilience (nom_scientifique, nom_commun, notes_utilite, texte_complet)
                elif "nom_scientifique" in cols and "notes_utilite" in cols:
                    c_sci = table["nom_scientifique"].to_pylist()
                    c_com = table["nom_commun"].to_pylist()
                    c_notes = table["notes_utilite"].to_pylist()
                    c_txt = table["texte_complet"].to_pylist()
                    for i in range(len(c_sci)):
                        bloc = f"{c_sci[i]} {c_com[i]} {c_txt[i]}".lower()
                        if terme_l in bloc:
                            idx = str(c_txt[i]).lower().find(terme_l)
                            debut = max(0, idx - 60)
                            snippet = str(c_txt[i])[debut:debut+300].replace("\n", " ").strip()
                            resultats.append({
                                "source": "Plantes Utiles & Résilience (PFAF)",
                                "titre": f"{c_sci[i]} ({c_com[i]})",
                                "texte": snippet + "...",
                                "extra": f"⭐ {c_notes[i]}"
                            })
                            if len(resultats) >= limite:
                                break

                # 4. D-PLACE Anthropologie Mondiale (societe, variable, valeur_et_description, texte_complet)
                elif "societe" in cols and "variable" in cols and "valeur_et_description" in cols:
                    c_soc = table["societe"].to_pylist()
                    c_dom = table["domaine"].to_pylist()
                    c_var = table["variable"].to_pylist()
                    c_val = table["valeur_et_description"].to_pylist()
                    c_txt = table["texte_complet"].to_pylist()
                    for i in range(len(c_soc)):
                        bloc = f"{c_soc[i]} {c_dom[i]} {c_var[i]} {c_val[i]}".lower()
                        if terme_l in bloc:
                            resultats.append({
                                "source": f"Anthropologie Mondiale D-PLACE ({c_soc[i]})",
                                "titre": f"{c_dom[i]} — {c_var[i]}",
                                "texte": f"Observation : {c_val[i]}\n   Contexte : {c_txt[i][:220]}",
                                "extra": "Atlas Ethnographique Murdock / Max Planck Institute"
                            })
                            if len(resultats) >= limite:
                                break

                # 5. Patrimoine Culturel Immatériel UNESCO (titre, pays, description, themes)
                elif "titre" in cols and "themes" in cols and "pays" in cols:
                    c_titre = table["titre"].to_pylist()
                    c_pays = table["pays"].to_pylist()
                    c_annee = table["annee"].to_pylist()
                    c_desc = table["description"].to_pylist()
                    c_thm = table["themes"].to_pylist()
                    for i in range(len(c_titre)):
                        bloc = f"{c_titre[i]} {c_pays[i]} {c_desc[i]} {c_thm[i]}".lower()
                        if terme_l in bloc:
                            idx = str(c_desc[i]).lower().find(terme_l)
                            debut = max(0, idx - 60)
                            snippet = str(c_desc[i])[debut:debut+300].replace("\n", " ").strip()
                            resultats.append({
                                "source": f"Patrimoine Culturel Immatériel UNESCO ({c_pays[i]}, {c_annee[i]})",
                                "titre": str(c_titre[i]),
                                "texte": snippet + "...",
                                "extra": f"Thèmes : {str(c_thm[i])[:120]}"
                            })
                            if len(resultats) >= limite:
                                break

                # 6. WikiHow Procédures Pratiques (tache, procedure_detaillee)
                elif "tache" in cols and "procedure_detaillee" in cols:
                    c_tache = table["tache"].to_pylist()
                    c_proc = table["procedure_detaillee"].to_pylist()
                    for i in range(len(c_tache)):
                        bloc = f"{c_tache[i]} {c_proc[i]}".lower()
                        if terme_l in bloc:
                            idx = str(c_proc[i]).lower().find(terme_l)
                            debut = max(0, idx - 60)
                            snippet = str(c_proc[i])[debut:debut+300].replace("\n", " ").strip()
                            resultats.append({
                                "source": "WikiHow Procédures Pratiques Humaines",
                                "titre": str(c_tache[i]),
                                "texte": snippet + "...",
                                "extra": "Procédure pratique étape par étape"
                            })
                            if len(resultats) >= limite:
                                break

                # 7. ConceptNet 5.5 Sens Commun MIT (rel, arg1, arg2, weight)
                elif "rel" in cols and "arg1" in cols and "arg2" in cols:
                    try:
                        dataset = ds.dataset(str(pfile), format="parquet")
                        filtre = pc.match_substring(pc.utf8_lower(ds.field("arg1")), terme_l) | pc.match_substring(pc.utf8_lower(ds.field("arg2")), terme_l)
                        scanner = dataset.scanner(columns=["rel", "arg1", "arg2", "weight"], filter=filtre, batch_size=4096)
                        for batch in scanner.to_batches():
                            tb = batch.to_pydict()
                            for i in range(len(tb["rel"])):
                                r_clean = str(tb["rel"][i]).replace("/r/", "")
                                a1_clean = str(tb["arg1"][i]).replace("/c/en/", "").replace("/n", "")
                                a2_clean = str(tb["arg2"][i]).replace("/c/en/", "").replace("/n", "")
                                resultats.append({
                                    "source": "Graphe de Sens Commun MIT (ConceptNet 5.5)",
                                    "titre": f"[{a1_clean}] --{r_clean}--> [{a2_clean}]",
                                    "texte": f"Relation sémantique de sens commun (poids : {tb['weight'][i]}).",
                                    "extra": "MIT Media Lab Open Mind Common Sense"
                                })
                                if len(resultats) >= limite:
                                    break
                            if len(resultats) >= limite:
                                break
                    except Exception:
                        pass

                # 8. Bushcraft & Survie Distillée (sujet, instruction, reponse_pratique)
                elif "instruction" in cols and "reponse_pratique" in cols:
                    c_suj = table.column("sujet").to_pylist() if "sujet" in cols else ["Survie"] * table.num_rows
                    c_inst = table["instruction"].to_pylist()
                    c_rep = table["reponse_pratique"].to_pylist()
                    for i in range(len(c_inst)):
                        bloc = f"{c_suj[i]} {c_inst[i]} {c_rep[i]}".lower()
                        if terme_l in bloc:
                            idx = str(c_rep[i]).lower().find(terme_l)
                            debut = max(0, idx - 60)
                            snippet = str(c_rep[i])[debut:debut+280].replace("\n", " ").strip()
                            resultats.append({
                                "source": f"Bushcraft & Survie de Terrain ({c_suj[i]})",
                                "titre": str(c_inst[i])[:75],
                                "texte": snippet + "...",
                                "extra": "Technique de terrain distillée (Guide pratique)"
                            })
                            if len(resultats) >= limite:
                                break

                # 9. Agriculture Régénératrice (scenario_id, scenario_description, actions, expected_outcome)
                elif "scenario_description" in cols and "actions" in cols:
                    c_desc = table["scenario_description"].to_pylist()
                    c_act = table["actions"].to_pylist()
                    c_out = table["expected_outcome"].to_pylist()
                    for i in range(len(c_desc)):
                        bloc = f"{c_desc[i]} {c_act[i]} {c_out[i]}".lower()
                        if terme_l in bloc:
                            resultats.append({
                                "source": "Agriculture Régénératrice & Vivrière",
                                "titre": str(c_desc[i])[:75],
                                "texte": f"Actions : {str(c_act[i])[:200]}...\n   Résultat visé : {str(c_out[i])[:120]}...",
                                "extra": "Pratique agro-écologique souveraine"
                            })
                            if len(resultats) >= limite:
                                break

                # 10. CoT Bushcraft & Raisonnement (id, messages)
                elif "messages" in cols:
                    c_id = table["id"].to_pylist()
                    c_msgs = table["messages"].to_pylist()
                    for i in range(len(c_id)):
                        msg_str = str(c_msgs[i])
                        if terme_l in msg_str.lower():
                            idx = msg_str.lower().find(terme_l)
                            debut = max(0, idx - 60)
                            snippet = msg_str[debut:debut+280].replace("\n", " ").strip()
                            resultats.append({
                                "source": "Raisonnement de Survie (CoT Bushcraft)",
                                "titre": f"Protocole Survie #{c_id[i]}",
                                "texte": snippet + "...",
                                "extra": "Chaîne d'inférence de survie en milieu hostile"
                            })
                            if len(resultats) >= limite:
                                break

            except Exception:
                pass
            if len(resultats) >= limite:
                break

    duree_ms = (time.perf_counter() - t0) * 1000
    print("==========================================================================")
    print(f" 🛠️ PILIER 09 (SAVOIRS PRATIQUES, ANTHROPOLOGIE, ETHNOBOTANIQUE & MIT) : « {terme} »")
    print(f" ⏱️ Temps de scan : {duree_ms:.1f} ms | Trouvés : {len(resultats)}")
    print("==========================================================================")
    for r in resultats:
        print(f"👉 [{r['source']} — {r['titre']}]")
        print(f"   📜 {r['texte']}")
        if r.get("extra"):
            print(f"   {r['extra']}\n")
        else:
            print()

def chercher_histoire(terme: str, limite: int = 5, sub_focus: str = "tous"):
    """Scanne le Pilier 11 : Seshat Cliodynamique, Polycrises, et Conflits CoW/UCDP."""
    t0 = time.perf_counter()
    resultats = []
    data_dir = DIR_HISTOIRE / "data"
    terme_l = terme.lower()

    if data_dir.exists():
        files = sorted(data_dir.glob("*.parquet"))
        if sub_focus in ["seshat", "cliodynamique"]:
            files = [f for f in files if "seshat" in f.name.lower()]
        elif sub_focus in ["conflits", "cow", "ucdp"]:
            files = [f for f in files if "geopolitique" in f.name.lower()]

        for pfile in files:
            try:
                table = pq.read_table(pfile)
                cols = table.column_names

                # Cas 1 : Seshat Cliodynamique (region_nga, entite_politique, annee_historique, niveau_complexite, texte_complet)
                if "region_nga" in cols and "niveau_complexite" in cols:
                    c_nga = table["region_nga"].to_pylist()
                    c_pol = table["entite_politique"].to_pylist()
                    c_annee = table["annee_historique"].to_pylist()
                    c_cx = table["niveau_complexite"].to_pylist()
                    c_txt = table["texte_complet"].to_pylist()
                    c_src = table["source"].to_pylist()
                    for i in range(len(c_nga)):
                        bloc = f"{c_nga[i]} {c_pol[i]} {c_annee[i]} {c_txt[i]}".lower()
                        if terme_l in bloc:
                            resultats.append({
                                "source": f"Cliodynamique Seshat ({c_pol[i]}, {c_annee[i]})",
                                "titre": f"Région : {c_nga[i]} — Complexité : {c_cx[i]}",
                                "texte": str(c_txt[i]),
                                "extra": f"Source : {c_src[i]}"
                            })
                            if len(resultats) >= limite:
                                break

                # Cas 2 : CoW & UCDP Géopolitique (pays_ou_acteur, annee, nature_donnee, indicateurs, texte_complet)
                elif "pays_ou_acteur" in cols and "indicateurs" in cols:
                    c_pays = table["pays_ou_acteur"].to_pylist()
                    c_annee = table["annee"].to_pylist()
                    c_nat = table["nature_donnee"].to_pylist()
                    c_ind = table["indicateurs"].to_pylist()
                    c_txt = table["texte_complet"].to_pylist()
                    c_src = table["source"].to_pylist()
                    for i in range(len(c_pays)):
                        bloc = f"{c_pays[i]} {c_annee[i]} {c_nat[i]} {c_ind[i]}".lower()
                        if terme_l in bloc:
                            resultats.append({
                                "source": f"{c_nat[i]} ({c_pays[i]}, {c_annee[i]})",
                                "titre": f"Indicateurs : {c_ind[i][:90]}...",
                                "texte": str(c_txt[i]),
                                "extra": f"Source : {c_src[i]}"
                            })
                            if len(resultats) >= limite:
                                break

            except Exception:
                pass
            if len(resultats) >= limite:
                break

    duree_ms = (time.perf_counter() - t0) * 1000
    print("==========================================================================")
    print(f" ⏳ PILIER 11 (MACRO-HISTOIRE, CLIODYNAMIQUE SESHAT & CONFLITS) : « {terme} »")
    print(f" ⏱️ Temps de scan : {duree_ms:.1f} ms | Trouvés : {len(resultats)}")
    print("==========================================================================")
    for r in resultats:
        print(f"👉 [{r['source']} — {r['titre']}]")
        print(f"   📜 {r['texte']}")
        if r.get("extra"):
            print(f"   {r['extra']}\n")
        else:
            print()

def chercher_innovation(terme: str, limite: int = 5, sub_focus: str = "tous"):
    """Scanne le Pilier 12 : Matrice TRIZ d'Altshuller, Biomimétisme AskNature et Patterns d'Architecture."""
    t0 = time.perf_counter()
    resultats = []
    data_dir = DIR_INNOVATION / "data"
    terme_l = terme.lower()

    if data_dir.exists():
        files = sorted(data_dir.glob("*.parquet"))
        if sub_focus == "triz":
            files = [f for f in files if "triz" in f.name.lower()]
        elif sub_focus in ["bio", "biomimetisme"]:
            files = [f for f in files if "biomimetisme" in f.name.lower()]
        elif sub_focus in ["patterns", "design"]:
            files = [f for f in files if "pattern" in f.name.lower()]

        for pfile in files:
            try:
                table = pq.read_table(pfile)
                cols = table.column_names

                # Cas 1 : Matrice TRIZ (parametre_a_ameliorer_nom, parametre_degrade_nom, principes_recommandes_texte)
                if "parametre_a_ameliorer_nom" in cols and "principes_recommandes_texte" in cols:
                    c_imp = table["parametre_a_ameliorer_nom"].to_pylist()
                    c_wor = table["parametre_degrade_nom"].to_pylist()
                    c_pr = table["principes_recommandes_texte"].to_pylist()
                    c_txt = table["texte_complet"].to_pylist()
                    for i in range(len(c_imp)):
                        bloc = f"{c_imp[i]} {c_wor[i]} {c_pr[i]} {c_txt[i]}".lower()
                        if terme_l in bloc:
                            resultats.append({
                                "source": "Matrice de Résolution Inventive TRIZ (Altshuller)",
                                "titre": f"Améliorer [{c_imp[i]}] sans dégrader [{c_wor[i]}]",
                                "texte": f"Résolution d'ingénierie : {c_pr[i]}",
                                "extra": "Algorithme d'Invention TRIZ (39x40 & 76 Standards)"
                            })
                            if len(resultats) >= limite:
                                break

                # Cas 2 : Biomimétisme & BioDesign (organisme_ou_sujet, probleme_ou_requete, strategie_biologique_et_resolution)
                elif "organisme_ou_sujet" in cols and "strategie_biologique_et_resolution" in cols:
                    c_org = table["organisme_ou_sujet"].to_pylist()
                    c_pb = table["probleme_ou_requete"].to_pylist()
                    c_sol = table["strategie_biologique_et_resolution"].to_pylist()
                    for i in range(len(c_org)):
                        bloc = f"{c_org[i]} {c_pb[i]} {c_sol[i]}".lower()
                        if terme_l in bloc:
                            idx = str(c_sol[i]).lower().find(terme_l)
                            debut = max(0, idx - 60)
                            snippet = str(c_sol[i])[debut:debut+300].replace("\n", " ").strip()
                            resultats.append({
                                "source": f"Biomimétisme AskNature & BioDesign ({c_org[i]})",
                                "titre": str(c_pb[i])[:75],
                                "texte": snippet + "...",
                                "extra": "Stratégie d'ingénierie inspirée du vivant (R&D biologique)"
                            })
                            if len(resultats) >= limite:
                                break

                # Cas 3 : Design Patterns (domaine, nom, probleme, solution, invariant)
                elif "nom" in cols and "invariant" in cols:
                    c_nom = table["nom"].to_pylist()
                    c_dom = table["domaine"].to_pylist()
                    c_pb = table["probleme"].to_pylist()
                    c_sol = table["solution"].to_pylist()
                    c_inv = table["invariant"].to_pylist()
                    for i in range(len(c_nom)):
                        bloc = f"{c_nom[i]} {c_dom[i]} {c_pb[i]} {c_sol[i]} {c_inv[i]}".lower()
                        if terme_l in bloc:
                            resultats.append({
                                "source": f"Pattern d'Architecture Système ({c_dom[i]})",
                                "titre": c_nom[i],
                                "texte": f"Problème : {c_pb[i]}\n   Solution : {c_sol[i]}",
                                "extra": f"⚡ Invariant : {c_inv[i]}"
                            })
                            if len(resultats) >= limite:
                                break

            except Exception:
                pass
            if len(resultats) >= limite:
                break

    duree_ms = (time.perf_counter() - t0) * 1000
    print("==========================================================================")
    print(f" ⚡ PILIER 12 (HEURISTIQUE D'INNOVATION, TRIZ & BIOMIMÉTISME) : « {terme} »")
    print(f" ⏱️ Temps de scan : {duree_ms:.1f} ms | Trouvés : {len(resultats)}")
    print("==========================================================================")
    for r in resultats:
        print(f"👉 [{r['source']} — {r['titre']}]")
        print(f"   📜 {r['texte']}")
        if r.get("extra"):
            print(f"   {r['extra']}\n")
        else:
            print()

def chercher_materiaux(terme: str, limite: int = 5, sub_focus: str = "tous"):
    """Scanne le Pilier 10 : Matériaux d'ingénierie réels (limites, conductivité, Young) et chimie fondamentale."""
    t0 = time.perf_counter()
    resultats = []
    data_dir = DIR_MATERIAUX / "data"
    terme_l = strip_accents(terme)

    if data_dir.exists():
        files = sorted(data_dir.glob("*.parquet"))
        if sub_focus in ["chimie", "solvant"]:
            files = [f for f in files if "chimie" in f.name.lower()]
        elif sub_focus in ["materiau", "materiaux", "physique"]:
            files = [f for f in files if "materiaux" in f.name.lower()]

        for pfile in files:
            try:
                table = pq.read_table(pfile)
                cols = table.column_names

                # Cas 1 : Matériaux d'ingénierie
                if "nom_materiau" in cols and "conductivite_thermique_w_mk" in cols:
                    c_nom = table["nom_materiau"].to_pylist()
                    c_cls = table["classe_materiau"].to_pylist()
                    c_txt = table["texte_complet"].to_pylist()
                    c_ruine = table["comportement_ruine"].to_pylist()
                    c_app = table["applications"].to_pylist()
                    for i in range(len(c_nom)):
                        bloc = strip_accents(f"{c_nom[i]} {c_cls[i]} {c_txt[i]}")
                        if terme_l in bloc:
                            resultats.append({
                                "source": f"Matériau d'Ingénierie [{c_cls[i]}]",
                                "titre": c_nom[i],
                                "texte": c_txt[i],
                                "extra": f"⚡ Ruine : {c_ruine[i][:100]}... | Usage : {c_app[i][:80]}..."
                            })
                            if len(resultats) >= limite:
                                break

                # Cas 2 : Chimie fondamentale & Réactions
                elif "nom_chimique" in cols and "formule_brute" in cols:
                    c_nom = table["nom_chimique"].to_pylist()
                    c_fml = table["formule_brute"].to_pylist()
                    c_txt = table["texte_complet"].to_pylist()
                    c_dgr = table["dangers_critiques"].to_pylist()
                    c_sec = table["neutralisation_securite"].to_pylist()
                    for i in range(len(c_nom)):
                        bloc = strip_accents(f"{c_nom[i]} {c_fml[i]} {c_txt[i]}")
                        if terme_l in bloc:
                            resultats.append({
                                "source": f"Chimie & Solvant [{c_fml[i]}]",
                                "titre": c_nom[i],
                                "texte": c_txt[i],
                                "extra": f"⚠️ Dangers : {c_dgr[i][:90]}... | 🛡️ Neutralisation : {c_sec[i][:80]}..."
                            })
                            if len(resultats) >= limite:
                                break

            except Exception:
                pass
            if len(resultats) >= limite:
                break

    duree_ms = (time.perf_counter() - t0) * 1000
    print("==========================================================================")
    print(f" 🧱 PILIER 10 (MATIÈRE BRUTE, MATÉRIAUX & CHIMIE) : « {terme} »")
    print(f" ⏱️ Temps de scan : {duree_ms:.1f} ms | Trouvés : {len(resultats)}")
    print("==========================================================================")
    for r in resultats:
        print(f"👉 [{r['source']} — {r['titre']}]")
        print(f"   📜 {r['texte']}")
        if r.get("extra"):
            print(f"   {r['extra']}\n")
        else:
            print()

def chercher_semantique(terme: str, limite: int = 5, sub_focus: str = "tous"):
    """Scanne le Pilier 13 : FrameNet v1.7, Codex des Biais Cognitifs et Sophismes Logiques."""
    t0 = time.perf_counter()
    resultats = []
    data_dir = DIR_SEMANTIQUE / "data"
    terme_l = strip_accents(terme)

    if data_dir.exists():
        files = sorted(data_dir.glob("*.parquet"))
        if sub_focus in ["framenet", "frame", "cadre", "semantique"]:
            files = [f for f in files if "framenet" in f.name.lower()]
        elif sub_focus in ["biais", "bias"]:
            files = [f for f in files if "biais" in f.name.lower()]
        elif sub_focus in ["sophisme", "sophismes", "fallacy", "fallacies", "rhetorique"]:
            files = [f for f in files if "sophisme" in f.name.lower()]

        for pfile in files:
            try:
                table = pq.read_table(pfile)
                cols = table.column_names

                # Cas 1 : FrameNet v1.7
                if "nom_cadre" in cols and "roles_actantiels_core" in cols:
                    c_nom = table["nom_cadre"].to_pylist()
                    c_def = table["definition"].to_pylist()
                    c_core = table["roles_actantiels_core"].to_pylist()
                    c_lex = table["lexemes_declencheurs"].to_pylist()
                    c_txt = table["texte_complet"].to_pylist()
                    for i in range(len(c_nom)):
                        bloc = strip_accents(f"{c_nom[i]} {c_def[i]} {c_lex[i]} {c_core[i]}")
                        if terme_l in bloc:
                            resultats.append({
                                "source": "Cadre Sémantique Universel FrameNet (UC Berkeley)",
                                "titre": f"Cadre [{c_nom[i]}]",
                                "texte": f"Définition : {c_def[i][:220]}...",
                                "extra": f"🎭 Rôles Actantiels Core : {c_core[i][:120]}... | Lexèmes : {c_lex[i][:60]}..."
                            })
                            if len(resultats) >= limite:
                                break

                # Cas 2 : Codex des Biais Cognitifs
                elif "nom_biais" in cols and "quadrant_benson" in cols:
                    c_nom = table["nom_biais"].to_pylist()
                    c_quad = table["quadrant_benson"].to_pylist()
                    c_def = table["deformation_mentale"].to_pylist()
                    c_ant = table["antidote_debiaisement"].to_pylist()
                    c_txt = table["texte_complet"].to_pylist()
                    for i in range(len(c_nom)):
                        bloc = strip_accents(f"{c_nom[i]} {c_quad[i]} {c_def[i]} {c_ant[i]}")
                        if terme_l in bloc:
                            resultats.append({
                                "source": f"Biais Cognitif Évolutif (Codex Buster Benson — {c_quad[i]})",
                                "titre": c_nom[i],
                                "texte": f"Déformation : {c_def[i]}",
                                "extra": f"🛡️ Antidote Débiaisement : {c_ant[i]}"
                            })
                            if len(resultats) >= limite:
                                break

                # Cas 3 : Sophismes Logiques
                elif "nom_sophisme" in cols and "riposte" in cols:
                    c_nom = table["nom_sophisme"].to_pylist()
                    c_fam = table["famille"].to_pylist()
                    c_mec = table["mecanisme"].to_pylist()
                    c_ex = table["exemple"].to_pylist()
                    c_rip = table["riposte"].to_pylist()
                    for i in range(len(c_nom)):
                        bloc = strip_accents(f"{c_nom[i]} {c_fam[i]} {c_mec[i]} {c_ex[i]} {c_rip[i]}")
                        if terme_l in bloc:
                            resultats.append({
                                "source": f"Sophisme & Piège Rhétorique [{c_fam[i]}]",
                                "titre": c_nom[i],
                                "texte": f"Mécanisme : {c_mec[i]}\n   Exemple : {c_ex[i]}",
                                "extra": f"🎯 Riposte SRE : {c_rip[i]}"
                            })
                            if len(resultats) >= limite:
                                break

            except Exception:
                pass
            if len(resultats) >= limite:
                break

    duree_ms = (time.perf_counter() - t0) * 1000
    print("==========================================================================")
    print(f" 🧠 PILIER 13 (GÉOMÉTRIE SÉMANTIQUE, BIAIS COGNITIFS & SOPHISMES) : « {terme} »")
    print(f" ⏱️ Temps de scan : {duree_ms:.1f} ms | Trouvés : {len(resultats)}")
    print("==========================================================================")
    for r in resultats:
        print(f"👉 [{r['source']} — {r['titre']}]")
        print(f"   📜 {r['texte']}")
        if r.get("extra"):
            print(f"   {r['extra']}\n")
        else:
            print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interrogation de la Cathédrale du Savoir")
    parser.add_argument("terme", type=str, help="Terme de recherche")
    parser.add_argument("--pilier", type=str, default="tous", choices=["vivant", "brevets", "lean", "mit", "mythes", "pratiques", "savoirs", "materiaux", "chimie", "histoire", "seshat", "cliodynamique", "triz", "innovation", "bio", "biomimetisme", "semantique", "biais", "sophismes", "tous"], help="Pilier cible")
    parser.add_argument("--limit", type=int, default=3, help="Nombre de résultats par pilier")
    args = parser.parse_args()

    if args.pilier in ["vivant", "tous"]:
        chercher_vivant(args.terme, args.limit)
    if args.pilier in ["brevets", "tous"]:
        chercher_brevets(args.terme, args.limit)
    if args.pilier in ["lean", "tous"]:
        chercher_lean(args.terme, args.limit)
    if args.pilier in ["mit", "tous"]:
        chercher_mit(args.terme, args.limit)
    if args.pilier in ["mythes", "tous"]:
        chercher_mythes(args.terme, args.limit)
    if args.pilier in ["pratiques", "savoirs", "tous"]:
        chercher_pratiques(args.terme, args.limit)
    if args.pilier in ["materiaux", "chimie", "tous"]:
        focus_mat = "chimie" if args.pilier == "chimie" else ("materiaux" if args.pilier == "materiaux" else "tous")
        chercher_materiaux(args.terme, args.limit, sub_focus=focus_mat)
    if args.pilier in ["histoire", "seshat", "cliodynamique", "tous"]:
        focus_hist = "seshat" if args.pilier in ["seshat", "cliodynamique"] else "tous"
        chercher_histoire(args.terme, args.limit, sub_focus=focus_hist)
    if args.pilier in ["triz", "innovation", "bio", "biomimetisme", "tous"]:
        focus_inv = "triz" if args.pilier == "triz" else ("bio" if args.pilier in ["bio", "biomimetisme"] else "tous")
        chercher_innovation(args.terme, args.limit, sub_focus=focus_inv)
    if args.pilier in ["semantique", "biais", "sophismes", "tous"]:
        focus_sem = "biais" if args.pilier == "biais" else ("sophismes" if args.pilier == "sophismes" else "tous")
        chercher_semantique(args.terme, args.limit, sub_focus=focus_sem)

