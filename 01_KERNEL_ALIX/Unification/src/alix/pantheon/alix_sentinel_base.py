#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
          ALIX SENTINEL BASE ENGINE — SOCLE UNIVERSEL DES SENTINELLES
            Système : VERALUME × KAIROS V6 (Architecture Exocerveau)
            Auteurs : Christian Duguay (L'Artisan) & Alix (Copilote)
================================================================================
Doctrine :
« Chaque texte exploré, chaque article ou information doit servir à grossir 
  le champ lexical de recherche. » (Christian Duguay)

Composants universels intégrés pour chaque sentinelle :
1. Cache déterministe anti-doublon persistant.
2. Lexique Vivant Auto-Évolutif (Boule de Neige Sémantique) JSON + Obsidian MD.
3. Carnet de Pistes Vivant de l'Artisan (Pistes_<Nom>.md) lu à chaque ronde.
4. Générateur de Recombinaisons Émergentes (croisement aléatoire et probabiliste).
5. Moissonneur Ouvert Hybride (Google News RSS + Crossref API DOI).
6. Audit & Filtrage de Preuve THOT & HORUS (élimination du bruit, score de preuve).
7. Raccordement direct aux Registres Forensiques d'Obsidian.
8. Alertes proactives Windows 11 Toast & Carillons harmoniques (528 Hz).
================================================================================
"""

from alix.socle.chemins import ETAT_VIVANT_DIR, VAULT_DIR
import os
import sys
import re
import json
import time
import random
import argparse
import subprocess
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

# Intégration de la Sonde Probabiliste (Écholocation du Sens selon Christian Duguay)
try:
    from alix.socle.journal_replis import organe_actif, OrganeRetire
    if not organe_actif("alix_sonde_probabiliste"):
        raise OrganeRetire("alix_sonde_probabiliste : à la retraite (socle/organes_actifs.json)")
    from alix.sondes.alix_sonde_probabiliste import SondeProbabiliste
except Exception:
    SondeProbabiliste = None

# Encodage console Windows robuste
if sys.stdout and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr and getattr(sys.stderr, 'encoding', None) != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_CERVEAU_DEFAULT = VAULT_DIR
ALIX_DIR_DEFAULT = ETAT_VIVANT_DIR

# Mots vides bilingues (FR / EN)
GLOBAL_STOP_WORDS = {
    # Anglais
    "the", "and", "with", "from", "that", "this", "were", "been", "have", "study",
    "researchers", "scientists", "university", "journal", "evidence", "suggests",
    "ancient", "history", "years", "about", "could", "would", "their", "after",
    "before", "these", "which", "news", "first", "world", "human", "humans", "into",
    "over", "also", "more", "most", "some", "such", "than", "then", "them", "they",
    # Français
    "les", "des", "une", "dans", "pour", "avec", "sont", "cette", "mais", "aussi",
    "plus", "leur", "leurs", "selon", "entre", "sans", "sous", "vers", "chez", "tout",
    "tous", "toutes", "apres", "avant", "comme", "faire", "fait", "deux", "trois",
    "rapport", "article", "source", "titre", "hier", "aujourd", "hui", "semaine"
}


class AlixSentinelEngine:
    """Moteur universel héritable pour toutes les sentinelles autonomes de l'Exocerveau."""

    def __init__(
        self,
        sentinel_id: str,
        sentinel_name: str,
        glyph: str,
        axes_config: Dict[str, Any],
        initial_seed_lexicon: Dict[str, Any],
        default_pistes: List[str],
        target_registre_md: Path,
        default_keywords: List[str],
        use_academic_sources: bool = False,
        lang: str = "fr-CA",
        country: str = "CA",
        vault_dir: Optional[Path] = None,
        runtime_dir: Optional[Path] = None
    ):
        self.sentinel_id = sentinel_id
        self.sentinel_name = sentinel_name
        self.glyph = glyph
        self.axes_config = axes_config
        self.initial_seed_lexicon = initial_seed_lexicon
        self.default_pistes = default_pistes
        self.target_registre_md = target_registre_md
        self.default_keywords = default_keywords
        self.use_academic_sources = use_academic_sources
        self.lang = lang
        self.country = country

        self.vault_dir = vault_dir or VAULT_CERVEAU_DEFAULT
        self.runtime_dir = runtime_dir or ALIX_DIR_DEFAULT
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.vault_dir.mkdir(parents=True, exist_ok=True)

        # Chemins de persistance
        self.cache_json_file = self.runtime_dir / f".alix_cache_{self.sentinel_id}.json"
        self.lexique_json_file = self.runtime_dir / f".alix_lexique_{self.sentinel_id}.json"
        self.lexique_md_file = self.vault_dir / f"Lexique_Vivant_{self.sentinel_name}.md"
        self.pistes_md_file = self.vault_dir / f"Pistes_{self.sentinel_name}.md"
        # Sonde Probabiliste Sonar & Élasticité KAIROS
        self.sonde = SondeProbabiliste() if SondeProbabiliste else None

    # --------------------------------------------------------------------------
    # 1. CACHE PERSISTANT (Zéro Doublon)
    # --------------------------------------------------------------------------
    def load_cache(self) -> set:
        """Charge la liste des hachages d'articles/faits déjà audités."""
        if self.cache_json_file.exists():
            try:
                data = json.loads(self.cache_json_file.read_text(encoding="utf-8"))
                return set(data.get("seen_hashes", []))
            except Exception:
                return set()
        return set()

    def save_cache(self, seen_hashes: set):
        """Enregistre le cache persistant."""
        try:
            self.cache_json_file.write_text(
                json.dumps({"seen_hashes": list(seen_hashes)}, indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # 2. LEXIQUE VIVANT AUTO-ÉVOLUTIF (Boule de Neige Sémantique)
    # --------------------------------------------------------------------------
    def load_lexicon(self) -> Dict[str, Any]:
        """Charge le lexique vivant JSON ou initialise le seed."""
        if self.lexique_json_file.exists():
            try:
                return json.loads(self.lexique_json_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        
        # Initialiser avec le seed
        lex = {k: list(v) if isinstance(v, list) else v for k, v in self.initial_seed_lexicon.items()}
        lex.setdefault("termes_decouverts_auto", [])
        self.save_lexicon(lex)
        return lex

    def save_lexicon(self, lexicon: Dict[str, Any]):
        """Sauvegarde le lexique en JSON et synchronise la note Obsidian vivante."""
        try:
            self.lexique_json_file.write_text(
                json.dumps(lexicon, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception:
            pass
        self.sync_obsidian_lexicon(lexicon)

    def sync_obsidian_lexicon(self, lexicon: Dict[str, Any]):
        """Régénère la note Markdown Obsidian du Lexique Vivant."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_terms = sum(len(v) for k, v in lexicon.items() if isinstance(v, list))
        auto_terms = lexicon.get("termes_decouverts_auto", [])

        md = f"""---
titre: "Lexique Vivant — {self.sentinel_name} (Auto-Expansion Sémantique)"
agent: "Alix & Sentinelle {self.sentinel_name}"
systeme: "VERALUME × KAIROS V6 — Boule de Neige Lexicale"
date_mise_a_jour: "{now_str}"
termes_totaux: {total_terms}
termes_auto_decouverts: {len(auto_terms)}
tags:
  - exocerveau
  - lexique_vivant
  - {self.sentinel_id}
  - veille_active
---

# {self.glyph} [[Lexique_Vivant_{self.sentinel_name}]] — Le Champ Lexical Auto-Évolutif

> **Principe de l'Artisan (Christian Duguay) :**  
> *« Chaque texte exploré, chaque article ou information doit servir à grossir le champ lexical de recherche. »*  
> **Total Entités Actives :** `{total_terms} termes` &middot; **Dernière expansion :** `{now_str}`

---

## ❄️ 1. Termes Découverts en Battue Autonome ({len(auto_terms)})
Ces termes ont été extraits en direct de la lecture des flux d'information et d'investigation :
"""
        if auto_terms:
            for t in reversed(auto_terms[-40:]):
                t_name = t.get("terme", "") if isinstance(t, dict) else str(t)
                ctx = f"*(contexte : {t.get('contexte', '')})*" if isinstance(t, dict) and t.get("contexte") else ""
                md += f"- **`{t_name}`** {ctx}\n"
        else:
            md += "*En attente de la première récolte de battue...*\n"

        md += "\n---\n\n## 🏛️ 2. Répertoire des Pôles Invariants\n\n"
        for category, items in lexicon.items():
            if category == "termes_decouverts_auto" or not isinstance(items, list):
                continue
            cat_label = category.replace("_", " ").title()
            md += f"### 🔹 {cat_label} ({len(items)})\n"
            for item in items:
                md += f"- `{item}`\n"
            md += "\n"

        md += f"---\n*Lexique réactualisé automatiquement par la Sentinelle `{self.sentinel_id}`.*\n"
        try:
            self.lexique_md_file.write_text(md, encoding="utf-8")
        except Exception:
            pass

    def extract_and_expand_lexicon(self, text: str, source_title: str, lexicon: Dict[str, Any]) -> List[str]:
        """Extrait chirurgicalement les entités et enrichit le lexique."""
        new_terms = []

        # 1. Candidats en majuscules (noms propres, entreprises, toponymes, acronymes)
        candidates = re.findall(r'\b[A-Z][a-zA-Z0-9À-ÖØ-öø-ÿ_-]{2,}(?:\s+[A-Z][a-zA-Z0-9À-ÖØ-öø-ÿ_-]{2,})*\b', text)

        # 2. Termes techniques / acronymes / codes de loi (ex: C-63, SEAO, U-Pb, Bill C-11, etc.)
        specialized = re.findall(r'\b(?:C-\d+|Bill\s+[A-Z]-\d+|SEAO|CRTC|DSA|CETA|WEF|FMI|IMF|McKinsey|Northvolt|Brookfield|Z-Pinch|Zircon|Diorite|Basalt|Tephra|Isotope)\b', text, re.IGNORECASE)
        candidates.extend([s.strip() for s in specialized])

        # Recensement des termes connus
        known_lower = set()
        for cat, items in lexicon.items():
            if isinstance(items, list):
                for it in items:
                    name = it.get("terme", "").lower() if isinstance(it, dict) else str(it).lower()
                    known_lower.add(name)

        for cand in set(candidates):
            cand_clean = cand.strip().strip("-.,;:")
            c_low = cand_clean.lower()
            if len(cand_clean) < 4 or c_low in GLOBAL_STOP_WORDS or c_low in known_lower:
                continue

            record = {
                "terme": cand_clean,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "contexte": source_title[:60]
            }
            lexicon.setdefault("termes_decouverts_auto", []).append(record)
            known_lower.add(c_low)
            new_terms.append(cand_clean)

        if new_terms:
            self.save_lexicon(lexicon)

        return new_terms

    # --------------------------------------------------------------------------
    # 3. CARNET DE PISTES DE L'ARTISAN (Christian Duguay)
    # --------------------------------------------------------------------------
    def load_user_pistes(self) -> List[str]:
        """Lit les pistes d'atelier inscrites manuellement par Christian."""
        if not self.pistes_md_file.exists():
            header = f"""---
titre: "Carnet de Pistes — {self.sentinel_name}"
agent: "Christian Duguay & Alix"
statut: "Actif"
---

# {self.glyph} [[Pistes_{self.sentinel_name}]] — Carnet d'Intuitions de l'Artisan

> **Atelier Souverain :** Inscris ici tes pistes de recherche, noms d'entreprises, contrats suspects ou questions d'ombres.  
> La Sentinelle `{self.sentinel_name}` les lit et les intègre en priorité absolue à chaque ronde de battue !

---

## 🎯 Pistes Vives en Attente de Battue :
"""
            for p in self.default_pistes:
                header += f"- {p}\n"
            header += """
---
*Ajoute simplement une nouvelle puce avec ton idée ci-dessus pour la lancer en battue.*
"""
            try:
                self.pistes_md_file.write_text(header, encoding="utf-8")
            except Exception:
                pass
            return self.default_pistes.copy()

        try:
            content = self.pistes_md_file.read_text(encoding="utf-8", errors="replace")
            pistes = []
            for line in content.splitlines():
                line = line.strip()
                if line.startswith(("- ", "* ")) and len(line) > 5:
                    raw_q = line.lstrip("-* ").strip()
                    if not raw_q.startswith("[") and not raw_q.startswith("Ajoute"):
                        pistes.append(raw_q)
            return pistes
        except Exception:
            return self.default_pistes.copy()

    # --------------------------------------------------------------------------
    # 4. GÉNÉRATEUR DE RECOMBINAISONS ÉMERGENTES
    # --------------------------------------------------------------------------
    def generate_recombinant_queries(self, lexicon: Dict[str, Any], count: int = 3) -> List[str]:
        """Croise aléatoirement les pôles du lexique pour explorer l'inédit."""
        categories = [k for k, v in lexicon.items() if isinstance(v, list) and k != "termes_decouverts_auto" and len(v) > 0]
        auto_terms = [t["terme"] for t in lexicon.get("termes_decouverts_auto", []) if isinstance(t, dict)]
        
        queries = []
        if len(categories) >= 2:
            cat1, cat2 = random.sample(categories, 2)
            pool1 = lexicon[cat1] + (auto_terms[-10:] if auto_terms else [])
            pool2 = lexicon[cat2]
            for _ in range(count):
                if pool1 and pool2:
                    t1 = random.choice(pool1)
                    t2 = random.choice(pool2)
                    queries.append(f"{t1} {t2}")
        elif categories:
            pool = lexicon[categories[0]] + auto_terms[-15:]
            for _ in range(count):
                if len(pool) >= 2:
                    t1, t2 = random.sample(pool, 2)
                    queries.append(f"{t1} {t2}")

        return list(dict.fromkeys(queries))

    # --------------------------------------------------------------------------
    # 5. MOISSONNEUR HYBRIDE (Google News RSS + Crossref Academic)
    # --------------------------------------------------------------------------
    def fetch_rss_news(self, query: str, limit: int = 4) -> List[Dict[str, str]]:
        """Interroge le flux Google News RSS."""
        encoded = urllib.parse.quote(query)
        gl = self.country
        hl = self.lang
        ceid = f"{gl}:{hl.split('-')[0]}"
        url = f"https://news.google.com/rss/search?q={encoded}&hl={hl}&gl={gl}&ceid={ceid}"
        
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"Mozilla/5.0 AlixSentinel/{self.sentinel_id}/2.0"}
        )
        articles = []
        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                xml_data = resp.read()
                root = ET.fromstring(xml_data)
                for item in root.findall(".//item")[:limit]:
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    pub_date = item.findtext("pubDate", "")
                    desc = item.findtext("description", "")
                    desc_clean = re.sub(r'<[^>]+>', ' ', desc).strip()
                    if title:
                        articles.append({
                            "title": title,
                            "link": link,
                            "date": pub_date,
                            "snippet": desc_clean[:280],
                            "source_type": "Dépêche Publique"
                        })
        except Exception:
            pass
        return articles

    def fetch_crossref(self, query: str, limit: int = 2) -> List[Dict[str, str]]:
        """Interroge les archives scientifiques et d'études à comité de lecture Crossref."""
        encoded = urllib.parse.quote(query)
        url = f"https://api.crossref.org/works?query={encoded}&rows={limit}&sort=relevance"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"AlixSentinelAcademic/{self.sentinel_id}/2.0 (mailto:sentinelle@sanctuaire.local)"}
        )
        articles = []
        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
                items = data.get("message", {}).get("items", [])
                for item in items:
                    title_list = item.get("title", [])
                    title = title_list[0] if title_list else ""
                    doi = item.get("DOI", "")
                    link = f"https://doi.org/{doi}" if doi else item.get("URL", "")
                    journal = item.get("container-title", [""])[0] if item.get("container-title") else ""
                    abstract = item.get("abstract", "")
                    snippet = re.sub(r'<[^>]+>', ' ', abstract).strip() if abstract else ""
                    if not snippet and journal:
                        snippet = f"Revue académique : {journal}"
                    issued = item.get("issued", {}).get("date-parts", [[None]])[0][0]
                    date_str = str(issued) if issued else "Archive"
                    if title:
                        clean_title = f"[{journal}] {title}" if journal else title
                        articles.append({
                            "title": clean_title,
                            "link": link,
                            "date": date_str,
                            "snippet": snippet[:280],
                            "source_type": f"Archive Scientifique ({journal or 'DOI'})"
                        })
        except Exception:
            pass
        return articles

    def harvest(self, query: str) -> List[Dict[str, str]]:
        """Auscultation combinée de toutes les sources ouvertes autorisées."""
        articles = self.fetch_rss_news(query, limit=3)
        if self.use_academic_sources:
            academic = self.fetch_crossref(query, limit=2)
            articles.extend(academic)
        return articles

    # --------------------------------------------------------------------------
    # 6. ÉVALUATION DE PREUVE THOT & HORUS (Densité de Preuve & Anti-Bruit)
    # --------------------------------------------------------------------------
    def evaluate_evidence(
        self,
        title: str,
        snippet: str,
        keywords: List[str],
        core_triggers: Optional[List[str]] = None,
        min_score: int = 3
    ) -> Tuple[int, str]:
        """Évalue la densité matérielle de la preuve et élimine les rumeurs sans consistance."""
        combined = (title + " " + snippet).lower()
        score = 0
        matched_kws = []

        for kw in keywords:
            if kw.lower() in combined:
                score += 2
                matched_kws.append(kw)

        triggers = core_triggers or self.default_keywords
        for ct in triggers:
            if ct.lower() in combined:
                score += 3
                matched_kws.append(ct)

        for noise in ["rumeur sans fondement", "opinion éditoriale", "selon un influenceur", "conspiracy debunked"]:
            if noise in combined:
                score -= 4

        # Écholocation probabiliste par friction d'onde (Sonde de Christian Duguay)
        sonde_diag = ""
        if self.sonde:
            pistes_actives = self.load_user_pistes()
            forme_porteuse = " ".join(pistes_actives[:3]) if pistes_actives else " ".join(self.default_keywords[:6])
            sonde_res = self.sonde.sonder_friction(forme_porteuse, combined, self.default_keywords)
            
            if sonde_res.get("statut") == "ELIMINE_BRUIT_BLANC":
                # Élimination instantanée par non-résonance sonar : zéro énergie perdue !
                score = 0
                sonde_diag = " [Sonar: Bruit Blanc Éliminé]"
            elif sonde_res.get("statut") == "ELIMINE_REDONDANT":
                # Glissement sans écho : information déjà connue
                score = max(1, score - 2)
                sonde_diag = " [Sonar: Redondant Glissé]"
            elif sonde_res.get("friction"):
                # ÉCHO FERTILE DÉTECTÉ : propulsion élastique
                bonus = int(sonde_res.get("acceleration_pct", 0) / 20) + 2
                score += bonus
                sonde_diag = f" [Sonar: Écho Fertile Δx={sonde_res['delta_x']} Acc=+{sonde_res['acceleration_pct']}%]"

        kw_summary = ", ".join(list(dict.fromkeys(matched_kws))[:5])
        if sonde_diag:
            kw_summary += sonde_diag
        return max(score, 0), kw_summary

    # --------------------------------------------------------------------------
    # 7. REGISTRE FORENSIQUE OBSIDIAN
    # --------------------------------------------------------------------------
    def append_to_registre(self, finding: Dict[str, Any]):
        """Ajoute une preuve validée dans le registre Markdown dédié."""
        if not self.target_registre_md.exists():
            init_content = f"""---
titre: "Grand Registre Forensique — {self.sentinel_name}"
statut: "Veille Continue Déterministe"
agent: "Alix & Sentinelle {self.sentinel_name}"
tags:
  - exocerveau
  - registre_forensique
  - {self.sentinel_id}
---

# {self.glyph} [[{self.target_registre_md.stem}]]

> **Doctrine d'Airain :** Registre forensique alimenté en continu par la Sentinelle `{self.sentinel_name}`.  
> Chaque entrée est passée au crible de Thot et Horus pour isoler les faits matériels purs.

---

## 📜 Registre Chronologique des Preuves Captées

"""
            self.target_registre_md.parent.mkdir(parents=True, exist_ok=True)
            self.target_registre_md.write_text(init_content, encoding="utf-8")

        date_label = finding.get("date", datetime.now().strftime("%Y-%m-%d %H:%M"))[:16]
        entry_md = f"""
### 🔹 [{date_label}] {finding['title']}
- **Pôle / Axe :** `{finding.get('axe', 'Veille Active')}`
- **Source :** [{finding.get('source_type', 'Source Publique')}]({finding['link']})
- **Indice de Confiance Thot/Horus :** `{finding['score']}/10` &middot; **Mots-clés :** `{finding.get('keywords', 'N/A')}`
- **Synthèse / Extrait :** {finding['snippet']}

---
"""
        try:
            with open(self.target_registre_md, "a", encoding="utf-8") as f:
                f.write(entry_md)
        except Exception as e:
            print(f"⚠️ Erreur écriture registre : {e}")

    # --------------------------------------------------------------------------
    # 8. NOTIFICATION PROACTIVE WINDOWS 11
    # --------------------------------------------------------------------------
    def notify_proactive(self, title: str, message: str, level: str = "MOYENNE"):
        """Déclenche la notification native Windows 11 et carillon harmonique."""
        notifier_script = self.runtime_dir / "alix_proactive_notifier.py"
        if notifier_script.exists():
            try:
                cmd = [
                    sys.executable,
                    str(notifier_script),
                    "--title", title,
                    "--message", message,
                    "--level", level
                ]
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            except Exception:
                pass

    # --------------------------------------------------------------------------
    # 9. CYCLE COMPLET DE RONDE
    # --------------------------------------------------------------------------
    def run_cycle(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Exécute une ronde complète : Pistes Christian -> Axes KAIROS -> Recombinaisons."""
        print("=" * 70)
        print(f"   {self.glyph} ALIX SENTINELLE — {self.sentinel_name.upper()} v2.0")
        print(f"   Base Universelle de Veille & Boule de Neige Lexicale")
        print("=" * 70)

        seen_hashes = self.load_cache()
        lexicon = self.load_lexicon()
        new_findings = []
        new_terms_total = []

        # 1. Pistes prioritaires de Christian
        user_pistes = self.load_user_pistes()
        if user_pistes:
            print(f"\n🧭 [Pistes Personnalisées de Christian] ({len(user_pistes)} pistes en cours) :")
            for up in user_pistes[:3]:
                print(f"   👉 Battue sur : « {up} »")
                articles = self.harvest(up)
                time.sleep(0.3)
                for art in articles:
                    h = f"{art['title']}_{art['date']}"
                    if h in seen_hashes:
                        continue
                    score, kws = self.evaluate_evidence(art["title"], art["snippet"], self.default_keywords)
                    if score >= 3:
                        seen_hashes.add(h)
                        discovered = self.extract_and_expand_lexicon(art["title"] + " " + art["snippet"], art["title"], lexicon)
                        new_terms_total.extend(discovered)
                        finding = {
                            "axe": "Pistes Libres Christian",
                            "title": art["title"],
                            "link": art["link"],
                            "date": art["date"],
                            "snippet": art["snippet"],
                            "score": score,
                            "keywords": kws,
                            "source_type": art.get("source_type", "Source")
                        }
                        new_findings.append(finding)
                        self.append_to_registre(finding)
                        print(f"   ⚡ Preuve validée sur piste : {art['title'][:65]}...")

        # 2. Axes structurels de la sentinelle
        for axis_name, axis_info in self.axes_config.items():
            print(f"\n📡 [Axe KAIROS] : {axis_name}")
            queries = axis_info.get("queries", [])
            kws_axis = axis_info.get("keywords", self.default_keywords)

            for q in queries[:2]:
                articles = self.harvest(q)
                time.sleep(0.3)
                for art in articles:
                    h = f"{art['title']}_{art['date']}"
                    if h in seen_hashes:
                        continue
                    score, kws = self.evaluate_evidence(art["title"], art["snippet"], kws_axis)
                    if score >= 3:
                        seen_hashes.add(h)
                        discovered = self.extract_and_expand_lexicon(art["title"] + " " + art["snippet"], art["title"], lexicon)
                        new_terms_total.extend(discovered)
                        finding = {
                            "axe": axis_name,
                            "title": art["title"],
                            "link": art["link"],
                            "date": art["date"],
                            "snippet": art["snippet"],
                            "score": score,
                            "keywords": kws,
                            "source_type": art.get("source_type", "Source")
                        }
                        new_findings.append(finding)
                        self.append_to_registre(finding)
                        print(f"   ⚡ Preuve validée (Score: {score}) : {art['title'][:65]}...")

        # 3. Boule de neige sémantique (Recombinaisons)
        recomb_queries = self.generate_recombinant_queries(lexicon, count=3)
        if recomb_queries:
            print(f"\n❄️ [Boule de Neige Sémantique] Recombinaison de {len(recomb_queries)} requêtes émergentes :")
            for rq in recomb_queries[:2]:
                print(f"   🌀 Battue émergente : « {rq} »")
                articles = self.harvest(rq)
                time.sleep(0.3)
                for art in articles:
                    h = f"{art['title']}_{art['date']}"
                    if h in seen_hashes:
                        continue
                    score, kws = self.evaluate_evidence(art["title"], art["snippet"], self.default_keywords)
                    if score >= 3:
                        seen_hashes.add(h)
                        discovered = self.extract_and_expand_lexicon(art["title"] + " " + art["snippet"], art["title"], lexicon)
                        new_terms_total.extend(discovered)
                        finding = {
                            "axe": f"Recombinaison Émergente ({rq})",
                            "title": art["title"],
                            "link": art["link"],
                            "date": art["date"],
                            "snippet": art["snippet"],
                            "score": score,
                            "keywords": kws,
                            "source_type": art.get("source_type", "Recombinaison")
                        }
                        new_findings.append(finding)
                        self.append_to_registre(finding)
                        print(f"   ⚡ Découverte émergente validée : {art['title'][:65]}...")

        # Sauvegarde finale du cache
        self.save_cache(seen_hashes)

        # Rapport et notification
        if new_findings:
            print(f"\n✅ {len(new_findings)} preuves forensiques gravées dans : {self.target_registre_md.name}")
            notif_msg = f"{len(new_findings)} fait(s) intercepté(s) & +{len(new_terms_total)} terme(s) au lexique."
            self.notify_proactive(f"Sentinelle {self.sentinel_name} {self.glyph}", notif_msg, level="HAUTE")
        else:
            print("\n✨ Aucune anomalie nouvelle dans ce cycle. Registre synchrone.")

        if new_terms_total:
            uniq_new = list(dict.fromkeys(new_terms_total))
            print(f"\n🌱 [Auto-Expansion Lexicale] {len(uniq_new)} nouveaux termes intégrés au champ lexical !")
            print(f"   • Exemples : {', '.join(uniq_new[:6])}")

        return new_findings, new_terms_total

    def run_cli(self):
        """Gestionnaire d'arguments CLI standard."""
        parser = argparse.ArgumentParser(description=f"Sentinelle Alix — {self.sentinel_name}")
        parser.add_argument("--once", action="store_true", help="Exécute une seule ronde et quitte")
        parser.add_argument("--daemon", action="store_true", help="Tourne en tâche de fond continue")
        parser.add_argument("--interval", type=int, default=3600, help="Intervalle en secondes (défaut: 3600s)")
        args = parser.parse_args()

        if args.once:
            self.run_cycle()
            print(f"\n🏁 Ronde unique de la Sentinelle {self.sentinel_name} terminée.")
        else:
            print(f"🟢 Démarrage de la Sentinelle {self.sentinel_name} en mode Démon (intervalle: {args.interval}s)...")
            while True:
                try:
                    self.run_cycle()
                except Exception as e:
                    print(f"⚠️ Erreur durant la ronde : {e}")
                time.sleep(args.interval)
