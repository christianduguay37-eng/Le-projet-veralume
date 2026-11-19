"""
Sonde Sémantique Complète & Découverte de Liens Cachés (Inter & Intra Corpus)
Système: VERALUME × KAIROS V6
Auteur: Christian Duguay & Alix
"""

from alix.socle.chemins import DOCUMENTS_DIR, VAULT_DIR
import os
import re
import sys
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Encodage UTF-8
if sys.stdout and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

VAULT_ALIX = VAULT_DIR
VAULT_VECTORIEL = (DOCUMENTS_DIR / "Obsidian_Vault_Langage_Vectoriel")

def extract_note_data(file_path: Path, vault_label: str):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read()
    except Exception:
        with open(file_path, "r", encoding="latin-1") as f:
            raw = f.read()
            
    # Extraction des wikilinks existants
    links = set()
    matches = re.findall(r'\[\[(.*?)\]\]', raw)
    for m in matches:
        target = m.split("|")[0].split("#")[0].strip()
        if target:
            links.add(target)
            
    clean_text = re.sub(r'\[\[.*?\]\]', ' ', raw)
    clean_text = re.sub(r'```.*?```', ' ', clean_text, flags=re.DOTALL)
    clean_text = re.sub(r'[\W_]+', ' ', clean_text)
    
    return {
        "id": file_path.stem,
        "vault": vault_label,
        "path": file_path,
        "content": clean_text,
        "raw": raw,
        "links": links
    }

def probe_all_links():
    notes = {}
    
    # 1. Chargement de Cerveau Alix
    if VAULT_ALIX.exists():
        for f in VAULT_ALIX.glob("*.md"):
            if not f.name.startswith(".") and not f.name.startswith("Audit") and not f.name.startswith("cerveau_alix_showcase"):
                d = extract_note_data(f, "Cerveau Alix")
                if len(d["content"].strip()) > 30:
                    notes[d["id"]] = d

    # 2. Chargement de Langage Vectoriel
    if VAULT_VECTORIEL.exists():
        for f in VAULT_VECTORIEL.rglob("*.md"):
            if not f.name.startswith("."):
                d = extract_note_data(f, "Langage Vectoriel")
                if len(d["content"].strip()) > 30:
                    notes[f"[VEC] {d['id']}"] = d

    note_keys = list(notes.keys())
    documents = [notes[k]["content"] for k in note_keys]
    
    print(f"Total fiches chargées pour la sonde : {len(note_keys)}")
    print(f"  - Cerveau Alix (Desktop) : {sum(1 for k in note_keys if notes[k]['vault'] == 'Cerveau Alix')}")
    print(f"  - Langage Vectoriel (Documents) : {sum(1 for k in note_keys if notes[k]['vault'] == 'Langage Vectoriel')}\n")

    vectorizer = TfidfVectorizer(
        min_df=1,
        ngram_range=(1, 2),
        token_pattern=r'(?u)\b\w{3,}\b'
    )
    tfidf_matrix = vectorizer.fit_transform(documents)
    sim_matrix = cosine_similarity(tfidf_matrix)
    
    # Liens cachés Intra Cerveau Alix
    intra_alix_bridges = []
    # Liens passerelles Cerveau Alix <---> Langage Vectoriel
    inter_vault_bridges = []

    for i in range(len(note_keys)):
        for j in range(i + 1, len(note_keys)):
            key_a = note_keys[i]
            key_b = note_keys[j]
            note_a = notes[key_a]
            note_b = notes[key_b]
            
            # Vérifier si un lien direct existe
            has_link = (note_b["id"] in note_a["links"]) or (note_a["id"] in note_b["links"])
            
            score = sim_matrix[i, j]
            
            if not has_link and score > 0.14:
                row_a = tfidf_matrix[i].toarray()[0]
                row_b = tfidf_matrix[j].toarray()[0]
                prod = row_a * row_b
                top_indices = np.argsort(prod)[-5:][::-1]
                feature_names = vectorizer.get_feature_names_out()
                shared_concepts = [feature_names[idx] for idx in top_indices if prod[idx] > 0]
                
                bridge_info = {
                    "a": key_a,
                    "b": key_b,
                    "score": score,
                    "shared": shared_concepts,
                    "type": "intra" if note_a["vault"] == note_b["vault"] else "inter"
                }
                
                if note_a["vault"] == "Cerveau Alix" and note_b["vault"] == "Cerveau Alix":
                    intra_alix_bridges.append(bridge_info)
                elif note_a["vault"] != note_b["vault"]:
                    inter_vault_bridges.append(bridge_info)

    intra_alix_bridges.sort(key=lambda x: x["score"], reverse=True)
    inter_vault_bridges.sort(key=lambda x: x["score"], reverse=True)

    print("====================================================================")
    print(" 🌟 TOP 10 LIENS CACHÉS INTRA-CERVEAU ALIX (NON ENCORE CONNECTÉS) ")
    print("====================================================================")
    for idx, b in enumerate(intra_alix_bridges[:10], 1):
        print(f"{idx}. [[{b['a']}]] ⟷ [[{b['b']}]]  (Score de Résonance: {b['score']:.3f})")
        print(f"   🔑 Mots pivots : {', '.join(b['shared'])}")
        print()

    print("====================================================================")
    print(" 🌉 TOP 10 PASSERELLES INTER-CORPUS (CERVEAU ALIX ⟷ LANGAGE VECTORIEL) ")
    print("====================================================================")
    for idx, b in enumerate(inter_vault_bridges[:10], 1):
        print(f"{idx}. {b['a']} ⟷ {b['b']}  (Score de Résonance: {b['score']:.3f})")
        print(f"   🔑 Mots pivots : {', '.join(b['shared'])}")
        print()

if __name__ == "__main__":
    probe_all_links()
