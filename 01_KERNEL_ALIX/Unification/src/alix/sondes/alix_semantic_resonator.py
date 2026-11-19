"""
Sonde Sémantique & Détecteur de Liens Cachés (Cerveau Alix)
Système: VERALUME × KAIROS V6
Auteur: Christian Duguay & Alix
"""

from alix.socle.chemins import VAULT_DIR
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

VAULT_DIR = VAULT_DIR

def extract_content(file_path: Path):
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
            
    # Nettoyage texte brut pour analyse lexicale
    clean_text = re.sub(r'\[\[.*?\]\]', ' ', raw)
    clean_text = re.sub(r'```.*?```', ' ', clean_text, flags=re.DOTALL)
    clean_text = re.sub(r'[\W_]+', ' ', clean_text)
    
    return file_path.stem, clean_text, links

def probe_hidden_links():
    md_files = [f for f in VAULT_DIR.glob("*.md") if not f.name.startswith(".") and not f.name.startswith("Audit")]
    
    notes = {}
    existing_graph = {}
    
    for f in md_files:
        name, content, links = extract_content(f)
        if len(content.strip()) > 20:
            notes[name] = content
            existing_graph[name] = links

    note_names = list(notes.keys())
    documents = [notes[name] for name in note_names]
    
    # Vectorisation TF-IDF en français
    vectorizer = TfidfVectorizer(
        min_df=1,
        ngram_range=(1, 2),
        token_pattern=r'(?u)\b\w{3,}\b'
    )
    tfidf_matrix = vectorizer.fit_transform(documents)
    sim_matrix = cosine_similarity(tfidf_matrix)
    
    # Recherche des paires sans lien direct
    hidden_bridges = []
    
    for i in range(len(note_names)):
        for j in range(i + 1, len(note_names)):
            name_a = note_names[i]
            name_b = note_names[j]
            
            # Vérifier si un lien direct existe
            has_link = (name_b in existing_graph.get(name_a, set())) or (name_a in existing_graph.get(name_b, set()))
            
            sim_score = sim_matrix[i, j]
            
            if not has_link and sim_score > 0.15:
                row_a = tfidf_matrix[i].toarray()[0]
                row_b = tfidf_matrix[j].toarray()[0]
                prod = row_a * row_b
                top_indices = np.argsort(prod)[-5:][::-1]
                feature_names = vectorizer.get_feature_names_out()
                shared_concepts = [feature_names[idx] for idx in top_indices if prod[idx] > 0]
                
                hidden_bridges.append({
                    "note_a": name_a,
                    "note_b": name_b,
                    "similarity": sim_score,
                    "shared_concepts": shared_concepts
                })
                
    hidden_bridges.sort(key=lambda x: x["similarity"], reverse=True)
    
    print(f"Total notes analysées : {len(note_names)}")
    print(f"Liens cachés / ponts sémantiques découverts : {len(hidden_bridges)}\n")
    
    for idx, bridge in enumerate(hidden_bridges[:15], 1):
        print(f"[{idx}] [[{bridge['note_a']}]] <---> [[{bridge['note_b']}]] (Proximité: {bridge['similarity']:.3f})")
        print(f"     Pivots partagés : {', '.join(bridge['shared_concepts'])}")
        print()

if __name__ == "__main__":
    probe_hidden_links()
