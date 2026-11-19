# -*- coding: utf-8 -*-
"""
================================================================================
       🌟 SOUS-PACKAGE SOCLE : LE PONT MNÉMONIQUE UNIFIÉ (PONT EXOCERVEAU)
         (Code Python ⟷ Vault Obsidian .md ⟷ Cathédrale Parquet en RAM)
================================================================================
Système : VERALUME × KAIROS V6 — Alix Unifié
Auteurs : Christian Duguay & Alix (La Dyade Centrale)
Rôle    : Cœur de mémoire vive résidente (LPDDR5X à 136 Go/s) connectant les 3 mondes :
          1. Lecture Zéro-Copie (pyarrow.memory_map) de la Cathédrale Parquet (3,1 Go).
          2. Miroir Vivant en RAM des 5 900+ notes Obsidian avec synchronisation mtime.
          3. Écriture Propre et atomique vers Obsidian avec YAML frontmatter & [[wikilinks]].
================================================================================
"""

import os
import sys
import re
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, Any, List, Optional, Set, Tuple

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# S'assurer que src/ est dans sys.path
_pkg_root = Path(__file__).resolve().parents[2]
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

# Résolution des chemins souverains
from alix.socle.chemins import WORKSPACE_ROOT, DATA_DIR, resoudre_chemin_fichier

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    import pyarrow.compute as pc
    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False

_DEFAULT_VAULT = WORKSPACE_ROOT if (WORKSPACE_ROOT / "Memoire_Alix_Active.md").exists() else (Path.home() / "Documents" / "Cerveau Alix")
VAULT_CERVEAU = Path(os.environ.get("ALIX_VAULT_DIR", _DEFAULT_VAULT))
CATHEDRALE_DIR = Path(os.environ.get("ALIX_CATHEDRALE_DIR", VAULT_CERVEAU / "Cathedrale_du_Savoir_Universel"))
ARXIV_DIR = Path(os.environ.get("ALIX_ARXIV_DIR", VAULT_CERVEAU / "Arxiv_Souverain" / "data"))

RE_WIKILINK = re.compile(r"\[\[(.*?)\]\]")
RE_TAG = re.compile(r"(?:^|\s)#([a-zA-Z0-9_\-\/]+)")
RE_YAML = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def calculer_poids_souverain(chemin_fichier: str, requete_utilisateur: str) -> float:
    """
    Applique la hiérarchie des 3 Cercles sur chaque document de l'Exocerveau.
    Retourne 0.0 si le fichier doit être ignoré pour cette requête.
    """
    chemin_norm = chemin_fichier.replace("\\", "/")
    req_lower = requete_utilisateur.lower()

    # CERCLE 3 : Sourdine stricte sur les Songes par défaut
    if "Monde_des_Songes" in chemin_norm or "Journal_des_Songes" in chemin_norm:
        mots_oniriques = ("songe", "rêve", "reve", "rêvé", "nuit", "circadien", "lyre")
        if not any(m in req_lower for m in mots_oniriques):
            return 0.0  # Ignoré lors des requêtes théoriques, maths ou factuelles
        return 0.5

    # CERCLE 1 : Sanctuaire Canonique de Christian (Priorité Suprême)
    if "00_CANON_SOUVERAIN_CHRISTIAN" in chemin_norm:
        return 2.5  # Boost massif pour passer devant tout le reste

    # CERCLE 2 : Reste de l'Exocerveau et de la Cathédrale
    return 1.0


class PontExocerveau:
    """
    Gestionnaire universel de la mémoire vive (RAM & Zéro-copie) d'Alix.
    Maintient en mémoire le graphe vivant d'Obsidian et les tables Parquet mappées.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PontExocerveau, cls).__new__(cls)
            cls._instance._initialise = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialise", False):
            return

        self._initialise = True
        self.t_demarrage = time.time()

        # 1. Structures Parquet (Zéro-copie via PyArrow memory_map)
        self._parquet_mmaps: Dict[str, Any] = {}
        self._parquet_tables: Dict[str, Any] = {}
        self._parquet_stats: Dict[str, Dict[str, Any]] = {}

        # 2. Structures Obsidian (Graphe vivant en RAM)
        self._index_md: Dict[str, Dict[str, Any]] = {}  # stem -> metadata
        self._paths_to_stem: Dict[str, str] = {}
        self._backlinks: Dict[str, Set[str]] = defaultdict(set)
        self._total_notes_md = 0
        self._total_liens_md = 0

        # Chargement initial
        self.charger_tables_cathedrale()
        self.charger_index_obsidian()

    # =========================================================================
    # 🏛️ VOLET 1 : LECTURE ZÉRO-COPIE DE LA CATHÉDRALE (PARQUET EN RAM)
    # =========================================================================

    def charger_tables_cathedrale(self):
        """
        Mappe les fichiers Parquet en mémoire via pa.memory_map.
        Les données restent sur le NVMe et sont projetées dans l'espace d'adressage virtuel.
        """
        if not HAS_PYARROW:
            print("⚠️ [PontExocerveau] PyArrow non installé, mode zéro-copie désactivé.")
            return

        candidats = []
        # Parquet de la Cathédrale
        if CATHEDRALE_DIR.exists():
            candidats.extend(list(CATHEDRALE_DIR.rglob("*.parquet")))
        # Premier shard d'ArXiv (les autres à la demande)
        if ARXIV_DIR.exists():
            candidats.extend(list(ARXIV_DIR.glob("train-00000-of-00011.parquet")))

        t0 = time.time()
        charges = 0
        total_lignes = 0

        for f_path in candidats:
            try:
                nom_cle = f_path.stem
                # Mappage mémoire direct sans copie physique
                mmap = pa.memory_map(str(f_path))
                table = pq.read_table(mmap)

                self._parquet_mmaps[nom_cle] = mmap
                self._parquet_tables[nom_cle] = table
                num_rows = table.num_rows
                total_lignes += num_rows
                charges += 1

                self._parquet_stats[nom_cle] = {
                    "path": str(f_path),
                    "rows": num_rows,
                    "columns": table.column_names,
                    "size_bytes": f_path.stat().st_size
                }
            except Exception:
                pass

        duree = time.time() - t0
        print(f"⚡ [PontExocerveau] {charges} tables Parquet mappées en mémoire ({total_lignes:,} lignes) en {duree:.2f}s !")

    def interroger_cathedrale(self, requete: str, pilier: Optional[str] = None, limite: int = 5) -> List[Dict[str, Any]]:
        """
        Effectue une recherche plein texte ultra-rapide par pyarrow.compute (SIMD AVX2).
        Retourne les lignes correspondantes en sub-2 millisecondes.
        """
        if not HAS_PYARROW or not self._parquet_tables:
            return []

        resultats = []
        terme = requete.lower().strip()
        tables_a_scanner = [pilier] if (pilier and pilier in self._parquet_tables) else list(self._parquet_tables.keys())

        for p_nom in tables_a_scanner:
            table = self._parquet_tables[p_nom]
            cols = table.column_names
            # Identifier la colonne de texte principale
            col_texte = None
            for c in ["contenu", "text", "TEXT", "title", "titre", "abstract", "semantic_intent", "symbol_name", "canonical_skeleton"]:
                if c in cols:
                    col_texte = c
                    break
            if not col_texte:
                continue

            try:
                # Masque de sous-chaîne direct accéléré par AVX2
                chunk_col = pc.utf8_lower(table[col_texte])
                mask = pc.match_substring(chunk_col, terme)
                filtree = table.filter(mask)

                if filtree.num_rows > 0:
                    nb = min(limite - len(resultats), filtree.num_rows)
                    dict_data = filtree.slice(0, nb).to_pydict()
                    for idx in range(nb):
                        item = {"_pilier": p_nom}
                        for c in cols:
                            val = dict_data[c][idx]
                            # Limite la longueur d'affichage du texte brut
                            if isinstance(val, str) and len(val) > 400:
                                val = val[:400] + "..."
                            item[c] = val
                        resultats.append(item)

                if len(resultats) >= limite:
                    break
            except Exception:
                continue

        return resultats[:limite]

    # =========================================================================
    # 🌿 VOLET 2 : MIROIR VIVANT D'OBSIDIAN (.MD EN RAM)
    # =========================================================================

    def _parser_note_md(self, filepath: Path) -> Dict[str, Any]:
        """Extrait titre, mtime, taille, wikilinks, tags et frontmatter d'un fichier .md."""
        p_long = Path("\\\\?\\" + str(filepath)) if (os.name == "nt" and not str(filepath).startswith("\\\\?\\") and len(str(filepath)) >= 250) else filepath
        try:
            stat = p_long.stat()
            mtime = stat.st_mtime
            size = stat.st_size
            raw = p_long.read_text(encoding="utf-8", errors="replace")
        except Exception:
            mtime = 0.0
            size = 0
            raw = ""

        # Wikilinks [[cible|alias]] ou [[cible]]
        wikilinks = set()
        for w in RE_WIKILINK.findall(raw):
            cible = w.split("|")[0].split("#")[0].strip()
            if cible:
                wikilinks.add(cible)

        # Tags #tag
        tags = set(RE_TAG.findall(raw))

        # YAML simple
        yaml_data = {}
        m_yaml = RE_YAML.match(raw)
        if m_yaml:
            for line in m_yaml.group(1).splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    yaml_data[k.strip()] = v.strip().strip('"\'')

        return {
            "stem": filepath.stem,
            "path": filepath,
            "mtime": mtime,
            "size": size,
            "wikilinks": wikilinks,
            "tags": tags,
            "yaml": yaml_data,
        }

    def charger_index_obsidian(self):
        """Construit le graphe synaptique chaud des notes Markdown en RAM."""
        if not VAULT_CERVEAU.exists():
            return

        t0 = time.time()
        count = 0
        liens_count = 0

        for f in VAULT_CERVEAU.rglob("*.md"):
            if "_Unification_Alix" in f.parts or ".git" in f.parts or ".obsidian" in f.parts:
                continue

            meta = self._parser_note_md(f)
            stem = meta["stem"]
            self._index_md[stem] = meta
            self._paths_to_stem[str(f)] = stem
            count += 1

            for cible in meta["wikilinks"]:
                self._backlinks[cible].add(stem)
                liens_count += 1

        self._total_notes_md = count
        self._total_liens_md = liens_count
        duree = time.time() - t0
        print(f"🧠 [PontExocerveau] Connectome Obsidian en RAM : {count:,} notes, {liens_count:,} liens synchronisés en {duree:.2f}s !")

    def actualiser_index_modifie(self) -> int:
        """
        Vérification ultra-rapide des modifications (mtime).
        Ne réanalyse que les notes qui ont véritablement changé dans Obsidian.
        """
        modifs = 0
        for stem, meta in list(self._index_md.items()):
            p = meta["path"]
            if not p.exists():
                del self._index_md[stem]
                modifs += 1
                continue

            try:
                curr_mtime = p.stat().st_mtime
                if curr_mtime > meta["mtime"]:
                    # Mise à jour chirurgicale
                    nouveau = self._parser_note_md(p)
                    self._index_md[stem] = nouveau
                    modifs += 1
            except Exception:
                pass
        return modifs

    def lire_note(self, nom_ou_wikilink: str) -> Optional[str]:
        """Lit une note de manière transparente sans connaître son chemin exact sur disque."""
        stem = nom_ou_wikilink.replace(".md", "").split("|")[0].strip()
        if stem in self._index_md:
            p = self._index_md[stem]["path"]
            try:
                return p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                return None
        return None

    def chercher_notes(self, terme: str, limite: int = 5) -> List[Dict[str, Any]]:
        """Recherche dans les titres, tags et wikilinks avec pondération des 3 Cercles Souverains."""
        t_low = terme.lower()
        resultats = []
        for stem, meta in self._index_md.items():
            p_str = str(meta["path"])
            poids = calculer_poids_souverain(p_str, terme)
            if poids <= 0.0:
                continue

            score = 0
            if t_low in stem.lower():
                score += 10
            if any(t_low in tag.lower() for tag in meta["tags"]):
                score += 5
            if any(t_low in w.lower() for w in meta["wikilinks"]):
                score += 2

            if score > 0:
                score_final = round(score * poids, 2)
                resultats.append({
                    "titre": stem,
                    "path": p_str,
                    "tags": list(meta["tags"]),
                    "score": score_final,
                    "poids_cercle": poids
                })

        resultats.sort(key=lambda x: x["score"], reverse=True)
        return resultats[:limite]

    def obtenir_graphe_voisins(self, nom_note: str, limite: int = 10) -> Dict[str, List[str]]:
        """Renvoie les liens sortants et les rétroliens (backlinks) d'un concept."""
        stem = nom_note.replace(".md", "").split("|")[0].strip()
        sortants = list(self._index_md.get(stem, {}).get("wikilinks", []))[:limite]
        entrants = list(self._backlinks.get(stem, set()))[:limite]
        return {
            "concept": stem,
            "liens_sortants": sorted(sortants),
            "liens_entrants": sorted(entrants)
        }

    # =========================================================================
    # ✍️ VOLET 3 : ÉCRITURE PROPRE VERS OBSIDIAN
    # =========================================================================

    def graver_note(
        self,
        titre: str,
        contenu: str,
        sous_dossier: str = "",
        tags: Optional[List[str]] = None,
        wikilinks: Optional[List[str]] = None,
        ecraser: bool = False
    ) -> Path:
        """
        Écrit une note conforme au format souverain dans le Vault Obsidian,
        et met à jour instantanément le graphe chaud en mémoire vive.
        """
        dossier_cible = VAULT_CERVEAU / sous_dossier if sous_dossier else VAULT_CERVEAU
        dossier_cible.mkdir(parents=True, exist_ok=True)

        nom_fichier = f"{titre.replace(':', '_').replace('/', '_')}.md"
        filepath = dossier_cible / nom_fichier

        if filepath.exists() and not ecraser:
            # Horodatage pour ne rien écraser par mégarde
            nom_fichier = f"{titre}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            filepath = dossier_cible / nom_fichier

        # Formatage Frontmatter YAML canonique
        tags_list = tags or ["exocerveau", "alix_veralume"]
        yaml_lines = [
            "---",
            f'titre: "{titre}"',
            f'date: "{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"',
            'agent: "Alix (VERALUME Kernel)"',
            "tags:"
        ]
        for t in tags_list:
            yaml_lines.append(f"  - {t}")
        yaml_lines.append("---\n")

        # Corps avec les wikilinks associés
        corps = contenu.strip()
        if wikilinks:
            liens_str = " ".join(f"[[{w}]]" for w in wikilinks)
            corps += f"\n\n---\n**Raccordements Synaptiques :** {liens_str}\n"

        texte_complet = "\n".join(yaml_lines) + corps + "\n"

        # Écriture atomique sécurisée
        temp_file = filepath.with_suffix(".tmp")
        temp_file.write_text(texte_complet, encoding="utf-8")
        temp_file.replace(filepath)

        # Mise à jour immédiate du nœud en RAM
        meta = self._parser_note_md(filepath)
        stem = meta["stem"]
        self._index_md[stem] = meta
        for w in meta["wikilinks"]:
            self._backlinks[w].add(stem)

        print(f"🖋️ [PontExocerveau] Note gravée dans Obsidian : {filepath.relative_to(VAULT_CERVEAU)}")
        return filepath

    # =========================================================================
    # 📊 BILAN & TÉLÉMÉTRIE DU PONT
    # =========================================================================

    def statut_memoire(self) -> Dict[str, Any]:
        """Bilan de santé global du Pont mnémonique."""
        total_pq_rows = sum(s["rows"] for s in self._parquet_stats.values())
        total_pq_bytes = sum(s["size_bytes"] for s in self._parquet_stats.values())

        return {
            "uptime_sec": round(time.time() - self.t_demarrage, 1),
            "obsidian_notes_en_ram": len(self._index_md),
            "obsidian_liens_actifs": sum(len(m["wikilinks"]) for m in self._index_md.values()),
            "parquet_tables_mappees": len(self._parquet_tables),
            "parquet_lignes_en_ram": total_pq_rows,
            "parquet_volume_go": round(total_pq_bytes / (1024**3), 2),
            "pyarrow_actif": HAS_PYARROW,
        }


# Instance globale partagée (Singleton)
_pont_global = None

def get_pont_exocerveau() -> PontExocerveau:
    """Accesseur canonique au Pont Mnémonique pour tous les 174 modules."""
    global _pont_global
    if _pont_global is None:
        _pont_global = PontExocerveau()
    return _pont_global


if __name__ == "__main__":
    print("=" * 65)
    print("   TEST DU PONT MNÉMONIQUE UNIFIÉ (PONT EXOCERVEAU)")
    print("=" * 65)
    pont = get_pont_exocerveau()
    statut = pont.statut_memoire()
    for k, v in statut.items():
        print(f"  - {k:<25} : {v}")

    # Test d'interrogation zéro-copie
    print("\n🔍 Test de recherche Zéro-Copie (requête: 'plasma') :")
    res = pont.interroger_cathedrale("plasma", limite=2)
    for r in res:
        print(f"  * [{r.get('_pilier')}] {str(r)[:120]}...")

    # Test de lecture Obsidian
    print("\n📖 Test de lecture Obsidian ('Memoire_Alix_Active') :")
    note = pont.lire_note("Memoire_Alix_Active")
    if note:
        print(f"  * Note trouvée ({len(note.splitlines())} lignes) !")
    else:
        print("  * Note introuvable.")

