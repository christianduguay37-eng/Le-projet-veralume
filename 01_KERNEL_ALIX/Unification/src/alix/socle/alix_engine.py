"""
================================================================================
                    ALIX COGNITIVE RESONATOR & RAG ENGINE v1.0
                  Système : VERALUME × KAIROS V6 (Architecture Exocerveau)
                  Auteur : Christian Duguay & Alix Assistant
================================================================================
"""

from alix.socle.chemins import DOCUMENTS_DIR, ETAT_VIVANT_DIR, VAULT_DIR
import os
import sys
import re
import json
import pickle
import time
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Fix encodage console Windows
if sys.stdout and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ================================================================================
# ARCHIPEL SOUVERAIN : CŒUR, ESPRIT & GREFFES D'ALIX
# ================================================================================
COEUR_VAULT = VAULT_DIR  # Scellé / Conscience
ESPRIT_VAULTS = [
    (DOCUMENTS_DIR / "Obsidian_Vault_Veralume_Platine"),  # Scellé / Raison pure
    (DOCUMENTS_DIR / "Obsidian_Vault_Veralume")          # Scellé / Archive historique
]
GREFFE_VAULTS = [
    (DOCUMENTS_DIR / "Obsidian_Vault_Pantheon_Doctrine"),       # Connaissances Alix N°01 (Tome 1)
    (DOCUMENTS_DIR / "Obsidian_Vault_Pantheon_Doctrine_Tome2"), # Connaissances Alix N°01 (Tome 2)
    (DOCUMENTS_DIR / "Obsidian_Vault_79_Skills"),               # Connaissances Alix N°02
    (DOCUMENTS_DIR / "Obsidian_Vault_Langage_Vectoriel")        # Connaissances Alix N°03
]

# Fédération totale des coffres
DEFAULT_VAULTS = [COEUR_VAULT] + ESPRIT_VAULTS + GREFFE_VAULTS

CACHE_FILE = (ETAT_VIVANT_DIR / ".alix_vault_cache.pkl")

# Mots vides français pour optimiser l'indexation sémantique
FRENCH_STOP_WORDS = [
    "alors", "au", "aucuns", "aussi", "autre", "avant", "avec", "avoir", "bon", "car", "ce", "cela",
    "ces", "ceux", "chaque", "ci", "comme", "comment", "dans", "des", "du", "dedans", "dehors",
    "depuis", "devrait", "doit", "donc", "dos", "droite", "début", "elle", "elles", "en", "encore",
    "essai", "est", "et", "eu", "fait", "faites", "fois", "font", "hors", "ici", "il", "ils", "je",
    "juste", "la", "le", "les", "leur", "là", "ma", "maintenant", "mais", "mes", "mien", "moins",
    "mon", "mot", "même", "ni", "nommés", "notre", "nous", "ou", "où", "par", "parce", "pas",
    "peut", "peu", "plupart", "pour", "pourquoi", "quand", "que", "quel", "quelle", "quelles",
    "quels", "qui", "sa", "sans", "ses", "seulement", "si", "sien", "son", "sont", "sous", "soyez",
    "sujet", "sur", "ta", "tandis", "tellement", "tels", "tes", "ton", "tous", "tout", "trop", "très",
    "tu", "voient", "vont", "votre", "vous", "vu", "ça", "étaient", "état", "étions", "été", "être"
]

class NoteDocument:
    def __init__(self, file_path: Path, vault_name: str):
        self.file_path = file_path
        self.vault_name = vault_name
        self.title = file_path.stem
        self.rel_path = str(file_path)
        self.mtime = file_path.stat().st_mtime
        self.raw_content = ""
        self.clean_text = ""
        self.wikilinks: List[str] = []
        self.headers: List[str] = []
        self.word_count = 0
        self._load()

    def _load(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.raw_content = f.read()
        except UnicodeDecodeError:
            try:
                with open(self.file_path, "r", encoding="latin-1") as f:
                    self.raw_content = f.read()
            except Exception:
                self.raw_content = ""

        # Extraction des wikilinks [[Cible]]
        matches = re.findall(r'\[\[(.*?)\]\]', self.raw_content)
        links = set()
        for m in matches:
            target = m.split("|")[0].split("#")[0].strip()
            if target:
                links.add(target)
        self.wikilinks = sorted(list(links))

        # Extraction des titres (# Titre)
        self.headers = re.findall(r'^#{1,4}\s+(.+)$', self.raw_content, flags=re.MULTILINE)

        # Nettoyage texte pour vectorisation
        text = re.sub(r'\[\[.*?\]\]', ' ', self.raw_content)
        text = re.sub(r'```.*?```', ' ', text, flags=re.DOTALL)
        text = re.sub(r'https?://\S+', ' ', text)
        text = re.sub(r'[\W_]+', ' ', text)
        self.clean_text = text.lower()
        self.word_count = len(self.raw_content.split())

class AlixEngine:
    def __init__(self, vaults: Optional[List[Path]] = None):
        self.vaults = vaults or [v for v in DEFAULT_VAULTS if v.exists()]
        self.notes: Dict[str, NoteDocument] = {}
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.note_names: List[str] = []
        self.vault_stats: Dict[str, int] = {}
        self.load_or_build_index()

    def _get_all_md_files(self) -> List[Tuple[Path, str]]:
        files = []
        for vault in self.vaults:
            v_name = vault.name
            for p in vault.rglob("*.md"):
                # Ignorer les dossiers système d'Obsidian
                if ".obsidian" in p.parts or ".trash" in p.parts:
                    continue
                files.append((p, v_name))
        return files

    def load_or_build_index(self, force_rebuild: bool = False):
        md_files = self._get_all_md_files()
        
        # Vérification cache
        if not force_rebuild and CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "rb") as f:
                    cache_data = pickle.load(f)
                
                cached_notes = cache_data.get("notes", {})
                cached_mtimes = {k: doc.mtime for k, doc in cached_notes.items()}
                
                # Vérifier si tous les fichiers actuels correspondent au cache
                is_valid = len(md_files) == len(cached_notes)
                if is_valid:
                    for p, _ in md_files:
                        key = str(p)
                        if key not in cached_mtimes or p.stat().st_mtime != cached_mtimes[key]:
                            is_valid = False
                            break
                            
                if is_valid:
                    self.notes = cached_notes
                    self.vectorizer = cache_data["vectorizer"]
                    self.tfidf_matrix = cache_data["tfidf_matrix"]
                    self.note_names = cache_data["note_names"]
                    self.vault_stats = cache_data["vault_stats"]
                    return
            except Exception:
                pass  # Reconstruire si le cache est corrompu

        # Reconstruction complète
        self.notes = {}
        self.vault_stats = {}
        for p, v_name in md_files:
            doc = NoteDocument(p, v_name)
            self.notes[str(p)] = doc
            self.vault_stats[v_name] = self.vault_stats.get(v_name, 0) + 1

        self.note_names = list(self.notes.keys())
        documents = [self.notes[k].clean_text for k in self.note_names]

        # TF-IDF multi-grammes (1-2 mots)
        self.vectorizer = TfidfVectorizer(
            min_df=1,
            ngram_range=(1, 2),
            stop_words=FRENCH_STOP_WORDS,
            token_pattern=r'(?u)\b\w{3,}\b'
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(documents)

        # Sauvegarde en cache
        try:
            with open(CACHE_FILE, "wb") as f:
                pickle.dump({
                    "notes": self.notes,
                    "vectorizer": self.vectorizer,
                    "tfidf_matrix": self.tfidf_matrix,
                    "note_names": self.note_names,
                    "vault_stats": self.vault_stats
                }, f)
        except Exception:
            pass

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Recherche sémantique + lexicale croisée"""
        if not self.vectorizer or not self.note_names:
            return []

        clean_q = re.sub(r'[\W_]+', ' ', query).lower().strip()
        q_vec = self.vectorizer.transform([clean_q])
        cos_sim = cosine_similarity(q_vec, self.tfidf_matrix).flatten()

        # Bonus pour correspondance exacte du titre ou mots-clés
        scores = []
        q_words = set(clean_q.split())
        for idx, sim in enumerate(cos_sim):
            doc = self.notes[self.note_names[idx]]
            score = float(sim)
            
            # Boost si requête dans le titre
            title_lower = doc.title.lower()
            if clean_q in title_lower:
                score += 0.4
            elif any(w in title_lower for w in q_words if len(w) > 3):
                score += 0.2
                
            scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in scores[:top_k]:
            if score <= 0.01:
                continue
            doc = self.notes[self.note_names[idx]]
            
            # Extraire le snippet le plus pertinent
            snippet = self._extract_best_snippet(doc.raw_content, query)
            
            results.append({
                "title": doc.title,
                "vault": doc.vault_name,
                "score": round(score, 4),
                "path": doc.rel_path,
                "snippet": snippet,
                "wikilinks": doc.wikilinks[:6],
                "headers": doc.headers[:4],
                "words": doc.word_count
            })

        return results

    def resonate(self, note_title: str, top_k: int = 6) -> List[Dict[str, Any]]:
        """Trouve les notes en plus forte résonance sémantique avec une note donnée"""
        target_idx = None
        for idx, name in enumerate(self.note_names):
            if self.notes[name].title.lower() == note_title.lower():
                target_idx = idx
                break
        
        if target_idx is None:
            # Recherche partielle
            for idx, name in enumerate(self.note_names):
                if note_title.lower() in self.notes[name].title.lower():
                    target_idx = idx
                    break

        if target_idx is None:
            return []

        target_doc = self.notes[self.note_names[target_idx]]
        row = self.tfidf_matrix[target_idx]
        sims = cosine_similarity(row, self.tfidf_matrix).flatten()
        
        indexed_sims = [(i, float(s)) for i, s in enumerate(sims) if i != target_idx]
        indexed_sims.sort(key=lambda x: x[1], reverse=True)
        
        resonances = []
        feature_names = self.vectorizer.get_feature_names_out()
        row_arr = row.toarray()[0]
        
        for idx, sim in indexed_sims[:top_k]:
            doc = self.notes[self.note_names[idx]]
            other_arr = self.tfidf_matrix[idx].toarray()[0]
            prod = row_arr * other_arr
            top_kw_idx = np.argsort(prod)[-4:][::-1]
            shared_pivots = [feature_names[i] for i in top_kw_idx if prod[i] > 0]
            
            is_linked = (doc.title in target_doc.wikilinks) or (target_doc.title in doc.wikilinks)
            
            resonances.append({
                "title": doc.title,
                "vault": doc.vault_name,
                "similarity": round(sim, 4),
                "is_direct_link": is_linked,
                "shared_pivots": shared_pivots,
                "path": doc.rel_path
            })
            
        return resonances

    def _extract_best_snippet(self, content: str, query: str, max_chars: int = 280) -> str:
        """Trouve le paragraphe le plus pertinent pour la requête"""
        paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 30]
        if not paragraphs:
            return content[:max_chars].strip() + "..."
            
        q_words = [w.lower() for w in re.sub(r'[\W_]+', ' ', query).split() if len(w) > 2]
        
        best_p = paragraphs[0]
        best_matches = -1
        
        for p in paragraphs:
            p_lower = p.lower()
            matches = sum(1 for w in q_words if w in p_lower)
            if matches > best_matches:
                best_matches = matches
                best_p = p
                
        # Nettoyage Markdown de base pour le snippet
        clean_snippet = re.sub(r'#+\s*', '', best_p)
        clean_snippet = re.sub(r'\*\*', '', clean_snippet)
        clean_snippet = ' '.join(clean_snippet.split())
        
        if len(clean_snippet) > max_chars:
            return clean_snippet[:max_chars] + "..."
        return clean_snippet

    def get_stats(self) -> Dict[str, Any]:
        total_words = sum(doc.word_count for doc in self.notes.values())
        total_links = sum(len(doc.wikilinks) for doc in self.notes.values())
        
        return {
            "total_notes": len(self.notes),
            "total_words": total_words,
            "total_wikilinks": total_links,
            "vaults": self.vault_stats
        }

def format_search_cli(results: List[Dict[str, Any]], query: str):
    print(f"\n=======================================================")
    print(f" 🔍 RÉSULTATS DE RÉSONANCE POUR : '{query}'")
    print(f"=======================================================\n")
    
    if not results:
        print("Aucune note trouvée en résonance directe.")
        return
        
    for i, res in enumerate(results, 1):
        print(f"[{i}] 📄 [[{res['title']}]] (Score: {res['score']})")
        print(f"    🏛️ Coffre   : {res['vault']}")
        print(f"    📖 Extrait  : \"{res['snippet']}\"")
        if res['wikilinks']:
            print(f"    🔗 Liens    : {', '.join(['[[' + l + ']]' for l in res['wikilinks'][:4]])}")
        print("-" * 55)

def format_resonate_cli(resonances: List[Dict[str, Any]], note_title: str):
    print(f"\n=======================================================")
    print(f" 🌌 PONT & RÉSONANCE SYNAPTIQUE POUR : [[{note_title}]]")
    print(f"=======================================================\n")
    
    if not resonances:
        print("Note introuvable ou aucune résonance détectée.")
        return
        
    for i, res in enumerate(resonances, 1):
        link_badge = "🔗 [Lien existant]" if res['is_direct_link'] else "✨ [Pont Caché Découvert]"
        print(f"[{i}] [[{res['title']}]] (Proximité: {res['similarity']}) — {link_badge}")
        print(f"    🏛️ Coffre  : {res['vault']}")
        if res['shared_pivots']:
            print(f"    🧬 Pivots  : {', '.join(res['shared_pivots'])}")
        print("-" * 55)

def main():
    parser = argparse.ArgumentParser(description="Alix Cognitive Resonator & Multi-Vault RAG Engine")
    parser.add_argument("command", choices=["query", "resonate", "stats", "rebuild"], help="Commande à exécuter")
    parser.add_argument("argument", nargs="?", default="", help="Terme de recherche ou titre de note")
    parser.add_argument("--top", type=int, default=5, help="Nombre de résultats")
    parser.add_argument("--json", action="store_true", help="Sortie au format JSON")
    
    args = parser.parse_args()
    
    t0 = time.time()
    engine = AlixEngine()
    
    if args.command == "rebuild":
        engine.load_or_build_index(force_rebuild=True)
        print(f"Index reconstruit avec succès en {time.time() - t0:.2f}s !")
        return
        
    if args.command == "stats":
        stats = engine.get_stats()
        if args.json:
            print(json.dumps(stats, indent=2, ensure_ascii=False))
        else:
            print("\n🌌 STATISTIQUES DU CERVEAU D'ALIX (4 COFFRES OBSIDIAN) 🌌")
            print("=" * 55)
            print(f"📚 Total de notes indexées : {stats['total_notes']}")
            print(f"✍️  Total de mots            : {stats['total_words']:,}")
            print(f"🔗 Total de liens synaptiques: {stats['total_wikilinks']:,}")
            print("\nRépartition par coffre :")
            for vault, count in stats['vaults'].items():
                print(f"  - {vault} : {count} notes")
            print("=" * 55)
            
    elif args.command == "query":
        if not args.argument:
            print("Veuillez spécifier une requête.")
            return
        results = engine.search(args.argument, top_k=args.top)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            format_search_cli(results, args.argument)
            print(f"Temps de réponse : {(time.time() - t0)*1000:.1f} ms")
            
    elif args.command == "resonate":
        if not args.argument:
            print("Veuillez spécifier un nom de note.")
            return
        resonances = engine.resonate(args.argument, top_k=args.top)
        if args.json:
            print(json.dumps(resonances, indent=2, ensure_ascii=False))
        else:
            format_resonate_cli(resonances, args.argument)
            print(f"Temps de réponse : {(time.time() - t0)*1000:.1f} ms")

if __name__ == "__main__":
    main()
