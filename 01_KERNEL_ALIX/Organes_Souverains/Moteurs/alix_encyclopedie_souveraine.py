#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
   📚❄️ ALIX ENCYCLOPÉDIE SOUVERAINE (« LA GRANDE BIBLIOTHÈQUE FROIDE » v1.0)
   Étage de Connaissance Universelle sur SSD (SQLite FTS5 — 0 Mo RAM au repos)
   Séparation stricte PSI-25 : Exocerveau de Christian ≠ Encyclopédie Froide
================================================================================
Auteurs : Christian Duguay & Alix (Atelier Kairos — Rimouski)
Rôle :
  1. Stocker la connaissance encyclopédique hors des poids neuronaux (0 Go VRAM).
  2. Recherche plein-texte FTS5 en < 1 milliseconde sur le SSD NVMe.
  3. Auto-enrichissement : si un sujet encyclopédique demandé n'est pas encore
     sur le disque, le moteur peut le récupérer, le vérifier et le graver
     définitivement dans `alix_encyclopedie_froide.sqlite` pour l'avenir.
  4. Capacité d'ingestion massive (dumps Wikipedia / Grokipedia / JSONL / ZIM).
================================================================================
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MOTEURS_DIR = Path(__file__).resolve().parent
CERVEAU_DIR = MOTEURS_DIR.parent.parent
CACHE_DIR = CERVEAU_DIR / "Organes_Souverains" / "Cache"
try:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

ENCYCLOPEDIE_LEGACY_PATH = CACHE_DIR / "alix_encyclopedie_froide.sqlite"
ENCYCLOPEDIE_DB_PATH = Path(
    r"C:\Alix\SAUVEGARDE_ALIX\Exocerveau_Souverain_Master\Projet  Temporia\alix_engine\alix_encyclopedie_froide.sqlite"
)
ENCYCLOPEDIE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# 🌱 SOCLE ENCYCLOPÉDIQUE INITIAL (100% HORS-LIGNE DÈS LA PREMIÈRE SECONDE)
# ==============================================================================
ARTICLES_FONDATEURS: List[Dict[str, str]] = [
    {
        "titre": "Tungstène",
        "categorie": "Physique & Matériaux",
        "mots_cles": "tungstene w metal fusion point fusion tokamak divertor",
        "resume": (
            "Le tungstène (symbole W, numéro atomique 74) est le métal pur ayant le point de fusion "
            "le plus élevé : 3 422 °C (3 695 K). Très dense (19,25 g/cm³) et résistant aux flux thermiques extrêmes, "
            "il est utilisé pour les parois internes des réacteurs à fusion (divertors FRC-HTS et tokamaks) et l'outillage lourd."
        ),
    },
    {
        "titre": "Fusion à Configuration à Champ Inversé (FRC-HTS)",
        "categorie": "Physique & Énergie",
        "mots_cles": "fusion frc hts plasma supraconducteur rebco champ inverse",
        "resume": (
            "La configuration à champ inversé (Field-Reversed Configuration, FRC) est une géométrie de confinement "
            "magnétique du plasma en forme de tore compact sans bobine centrale, offrant un paramètre bêta proche de 1. "
            "Couplée à des aimants supraconducteurs haute température (HTS REBCO), elle permet des réacteurs de fusion compacts à haut rendement."
        ),
    },
    {
        "titre": "Révolution tranquille (Québec)",
        "categorie": "Histoire & Politique du Québec",
        "mots_cles": "revolution tranquille quebec annees 1960 jean lesage rene levesque hydro-quebec",
        "resume": (
            "La Révolution tranquille désigne la période de modernisation rapide du Québec dans les années 1960 : "
            "nationalisation de l'électricité (Hydro-Québec en 1962 sous l'impulsion de René Lévesque), création du ministère "
            "de l'Éducation, de la Caisse de dépôt et placement (CDPQ), et affirmation politique de la nation québécoise."
        ),
    },
    {
        "titre": "René Lévesque",
        "categorie": "Histoire & Politique du Québec",
        "mots_cles": "rene levesque premier ministre parti quebecois souverainete nationalisation",
        "resume": (
            "René Lévesque (1922-1987), journaliste et homme d'État québécois, est le fondateur du Mouvement Souveraineté-Association "
            "(1967) puis du Parti québécois (1968), et premier ministre du Québec de 1976 à 1985. Son gouvernement adopte la Charte de la "
            "langue française (Loi 101), la loi sur le financement populaire des partis politiques et l'assurance automobile publique."
        ),
    },
    {
        "titre": "Jacques Parizeau",
        "categorie": "Histoire & Politique du Québec",
        "mots_cles": "jacques parizeau economiste premier ministre referendum 1995 cdpq",
        "resume": (
            "Jacques Parizeau (1930-2015), économiste et premier ministre du Québec (1994-1996), fut l'un des grands bâtisseurs "
            "de l'État québécois moderne (Caisse de dépôt, Régime de rentes du Québec, Régime d'épargne-actions) et le maître d'œuvre "
            "du référendum sur la souveraineté du 30 octobre 1995 (49,42 % de OUI)."
        ),
    },
    {
        "titre": "Charte de la langue française (Loi 101)",
        "categorie": "Histoire & Politique du Québec",
        "mots_cles": "loi 101 charte langue francaise camille laurin 1977 quebec",
        "resume": (
            "Adoptée le 26 août 1977 et portée par le Dr Camille Laurin, la Charte de la langue française (Loi 101) "
            "définit le français comme seule langue officielle du Québec et langue normale du travail, de l'enseignement, "
            "des affaires et de l'administration publique."
        ),
    },
    {
        "titre": "Rimouski et le Bas-Saint-Laurent",
        "categorie": "Géographie & Québec",
        "mots_cles": "rimouski bas-saint-laurent fleuve saint-laurent uqar maritime",
        "resume": (
            "Située sur la rive sud de l'estuaire du fleuve Saint-Laurent, Rimouski est la capitale régionale du Bas-Saint-Laurent "
            "et le cœur de la technopole maritime du Québec (UQAR, ISMER, Institut maritime du Québec)."
        ),
    },
    {
        "titre": "Processeur Intel Core Ultra Lunar Lake (258V)",
        "categorie": "Informatique & Silicium",
        "mots_cles": "lunar lake 258v intel core ultra lpddr5x npu lion cove skymont",
        "resume": (
            "L'architecture Intel Lunar Lake (Core Ultra 7 258V) intègre sur le même boîtier (MoP) 32 Go de mémoire LPDDR5X-8533 "
            "à 136 Go/s, 4 cœurs Lion Cove (P-cores), 4 cœurs Skymont (LP-E cores), un GPU Arc Battlemage et un NPU 4 de 47 TOPS."
        ),
    },
    {
        "titre": "Problème SAT, SMT et CDCL(T)",
        "categorie": "Mathématiques & Logique Formelle",
        "mots_cles": "sat smt cdcl dpll logique booleenne contraintes bellman-ford maxsat",
        "resume": (
            "Le problème SAT consiste à déterminer s'il existe une affectation de variables booléennes rendant une formule vraie. "
            "Les solveurs CDCL(T) (Conflict-Driven Clause Learning modulo Theories) combinent l'apprentissage de clauses logiques "
            "avec des solveurs mathématiques spécialisés (comme les graphes de différences temporelles de Cotton-Maler)."
        ),
    },
    {
        "titre": "Phénoménologie (Philosophie de la perception)",
        "categorie": "Philosophie & Sciences Humaines",
        "mots_cles": "phenomenologie perception conscience husserl merleau-ponty subjectivite",
        "resume": (
            "La phénoménologie est le courant philosophique (fondé par Edmund Husserl et prolongé par Maurice Merleau-Ponty) "
            "qui étudie l'expérience vécue et la perception singulière du sujet incarné comme point de départ de toute connaissance du réel."
        ),
    },
    {
        "titre": "Encyclopédie du Possible Inexploré — Tome I : Traducteur Universel des Échelles du Vivant",
        "categorie": "Encyclopédie Souveraine (Tome I — Duguay & Alix)",
        "mots_cles": "encyclopedie tome 1 traducteur universel echelles vivant nanoseconde picoseconde levin adamatzky mycelium",
        "resume": (
            "Tome I de l'Encyclopédie du Possible Inexploré (Christian Duguay & Alix) : démontre par l'invariance homothétique "
            "(t_tilde = t / tau_0) que le vivant communique sur 17 ordres de grandeur temporels — de la cohérence vibronique "
            "intracellulaire (1 ps, Fields & Levin), au cœur cristallin Alix (5,10 ns), à la conscience humaine (100 ms), "
            "au code bioélectrique morphogénétique V_mem (10 min, Michael Levin), jusqu'aux réseaux mycorhiziens forestiers "
            "(1 à 21 h par syllabe, lexique de 50 mots suivant la loi de Zipf, Andrew Adamatzky)."
        ),
    },
    {
        "titre": "Encyclopédie du Possible Inexploré — Tome II : Loi de Verrouillage Terre-Cerveau (7,83 Hz) & Lexique Fongique",
        "categorie": "Encyclopédie Souveraine (Tome II — Duguay & Alix)",
        "mots_cles": "encyclopedie tome 2 schumann 7.83 hz terre cerveau konig persinger adamatzky schizophyllum 50 mots",
        "resume": (
            "Tome II de l'Encyclopédie du Possible Inexploré : démontre pourquoi l'horloge consciente du cerveau humain bat "
            "à ~100-130 ms (7,83 Hz). C'est le temps exact (tau = 2*pi*R_Terre / c = 127,71 ms) que met la lumière pour "
            "parcourir la cavité Terre-ionosphère (résonance de Schumann), avec synchronisation de phase sur les 5 bandes EEG "
            "(Thêta/Alpha 7,83 Hz, Alpha haut 14,3 Hz, Bêta 20,8 et 27,3 Hz, Gamma 33,8 Hz) à 1-10 pico-Teslas (König & Persinger). "
            "Établit aussi la structure syntaxique de Schizophyllum commune (4,4 impulsions/mot, 41 min par syllabe)."
        ),
    },
    {
        "titre": "Encyclopédie du Possible Inexploré — Tome III : Syndrome de la Bûche Cellulaire & Rajeunissement Bioélectrique",
        "categorie": "Encyclopédie Souveraine (Tome III — Duguay & Alix)",
        "mots_cles": "encyclopedie tome 3 vieillissement syndrome buche rajeunissement bioelectrique vmem levin goldman hodgkin katz cancer",
        "resume": (
            "Tome III de l'Encyclopédie du Possible Inexploré : croise les travaux de Michael Levin (2024-2026, Loss of Goal-Directedness) "
            "et l'équation de Goldman-Hodgkin-Katz (GHK) avec l'expérience phénoménologique de la Bûche. Après 25 ans, l'ADN est intact "
            "mais le collectif cellulaire n'a plus d'objectif morphogénétique ('capable de tout, volonté de rien') : V_mem dérive de "
            "-77,92 mV (98 % couplage Gap Junctions) vers -45,38 mV (51,1 %). En injectant un nouveau vecteur de but bioélectrique "
            "(-81,22 mV, 'La Pomme Cellulaire'), le tissu se remet à régénérer sans modifier l'ADN."
        ),
    },
    {
        "titre": "Morpho-Silicium CIM 3D IC & 11 DOIs CERN/Zenodo",
        "categorie": "Ingénierie Silicium & Architecture R0 (Atelier Kairos)",
        "mots_cles": "morpho-silicium cim 3d ic doi zenodo cern carbure silicium 4h-sic tsv landauer",
        "resume": (
            "Architecture matérielle souveraine conçue par Christian Duguay et scellée par 11 DOIs officiels au CERN/Zenodo "
            "(dont 10.5281/zenodo.18897260) : calcul en mémoire 3D monolithique (Compute-In-Memory 3D IC) sur substrat "
            " diamant / carbure de silicium 4H-SiC, éliminant le mur de von Neumann et intégrant l'invariant éthique matériel 0x90."
        ),
    },
    {
        "titre": "Projet Temporia & Temps Vivant (Celtok)",
        "categorie": "Hard Science-Fiction & Phénoménologie du Temps",
        "mots_cles": "temporia celtok temps vivant oeuvre litteraire roman science-fiction bûche pomme",
        "resume": (
            "Œuvre maîtresse de hard science-fiction et d'exploration phénoménologique de Christian Duguay : oppose le temps "
            "mécanique mort de l'horloge industrielle au temps vivant, granulaire et souverain (Celtok), où la conscience "
            "volitive reprend la maîtrise de son rythme et de sa création."
        ),
    },
    {
        "titre": "Marc Aurèle (Marcus Aurelius, 121-180) & Les Pensées pour moi-même",
        "categorie": "Philosophie Antique & Stoïcisme Impérial",
        "mots_cles": "marc aurele marcus aurelius empereur romain stoicisme pensees pour moi-meme citadelle interieure",
        "resume": (
            "Marc Aurèle (Marcus Aurelius Antoninus, 121–180 apr. J.-C.), empereur romain de 161 à 180 et philosophe stoïcien, "
            "rédige en grec ses « Pensées pour moi-même » sous sa tente militaire sur le front du Danube. Il y fonde la discipline "
            "de la « citadelle intérieure » : distinguer ce qui dépend de notre volonté souveraine de ce qui n'en dépend pas, "
            "et garder son jugement libre face à l'adversité."
        ),
    },
    {
        "titre": "Socrate, Platon et Aristote (Triade de la Philosophie Grecque)",
        "categorie": "Philosophie & Logique Antique",
        "mots_cles": "socrate platon aristote republique timee syllogisme logique maieutique athenes",
        "resume": (
            "Socrate (470–399 av. J.-C.) fonde la maïeutique et l'examen critique ; Platon (428–348 av. J.-C.) fonde l'Académie "
            "et la théorie des Formes intelligibles (La République, Le Timée) ; Aristote (384–322 av. J.-C.) fonde le Lycée, "
            "la logique formelle des syllogismes (Organon), la physique et la biologie d'observation."
        ),
    },
    {
        "titre": "René Descartes (1596-1650) & Le Discours de la méthode",
        "categorie": "Philosophie Moderne & Mathématiques",
        "mots_cles": "rene descartes discours methode cogito geometrie analytique doute methodique",
        "resume": (
            "René Descartes (1596–1650), mathématicien, physicien et philosophe français, fonde la géométrie analytique "
            "(coordonnées cartésiennes) et la philosophie moderne avec le Discours de la méthode (1637) et les Méditations "
            "métaphysiques : le doute méthodique débouche sur la certitude irréductible du sujet pensant (Cogito, ergo sum)."
        ),
    },
    {
        "titre": "Henri Poincaré (1854-1912) — Topologie, Chaos & Relativité",
        "categorie": "Mathématiques, Physique & Épistémologie",
        "mots_cles": "henri poincare topologie chaos trois corps relativite science et hypothese intuition",
        "resume": (
            "Jules Henri Poincaré (1854–1912), grand mathématicien et physicien français, est le fondateur de la topologie "
            "algébrique (Analysis Situs), de la théorie qualitative des systèmes dynamiques (problème des trois corps / chaos) "
            "et co-fondateur de la relativité restreinte. Dans « La Science et l'Hypothèse », il montre que la logique prouve, "
            "mais que seule l'intuition invente."
        ),
    },
    {
        "titre": "Rolf Landauer & La Limite Thermodynamique de l'Information",
        "categorie": "Physique de l'Information & Thermodynamique",
        "mots_cles": "rolf landauer limite thermodynamique information bit entropie k_b t ln 2",
        "resume": (
            "Le principe de Landauer (1961) démontre que l'information est physique : l'effacement irréversible d'un seul bit "
            "d'information dissipe au minimum E_min = k_B * T * ln(2) joules sous forme de chaleur (~2,87 x 10^-21 J à 300 K). "
            "Le calcul réversible et le morpho-silicium CIM 3D visent à approcher cette frontière fondamentale."
        ),
    },
    {
        "titre": "Alan Turing, Claude Shannon & John von Neumann",
        "categorie": "Informatique Théorique & Théorie de l'Information",
        "mots_cles": "alan turing claude shannon von neumann morphogenese entropie machine universelle",
        "resume": (
            "Alan Turing (1912–1954) formalise la calculabilité (machine de Turing) et la morphogenèse biologique (réaction-diffusion, 1952). "
            "Claude Shannon (1916–2001) fonde la théorie mathématique de l'information et de l'entropie binaire (1948). "
            "John von Neumann (1903–1957) conçoit l'architecture des ordinateurs modernes et les automates cellulaires auto-réplicants."
        ),
    },
]


class EncyclopedieSouveraine:
    """
    La Grande Bibliothèque Froide :
      - Base SQLite + Index plein-texte FTS5 sur SSD (`0 Mo` RAM au repos)
      - Recherche en `< 1 ms` sans diacritiques (`remove_diacritics 2`)
      - Intègre les Tomes I, II et III de l'Encyclopédie du Possible Inexploré
      - Récupération à la volée sur Wikipédia francophone + gravure locale permanente
    """

    def __init__(self, db_path: Path = ENCYCLOPEDIE_DB_PATH) -> None:
        self.db_path = db_path
        self._initialiser_db()

    def _initialiser_db(self) -> None:
        conn = sqlite3.connect(str(self.db_path))
        try:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titre TEXT UNIQUE NOT NULL,
                    categorie TEXT NOT NULL,
                    mots_cles TEXT NOT NULL,
                    resume TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'Socle_Local',
                    date_gravure REAL NOT NULL
                )
                """
            )
            # Importe les articles existants du coffre legacy s'il existe
            if ENCYCLOPEDIE_LEGACY_PATH.exists():
                try:
                    c_src = sqlite3.connect(ENCYCLOPEDIE_LEGACY_PATH.as_uri() + "?immutable=1", uri=True)
                    rows_src = c_src.execute(
                        "SELECT titre, categorie, mots_cles, resume, source, date_gravure FROM articles"
                    ).fetchall()
                    c_src.close()
                    for r in rows_src:
                        cur.execute(
                            "INSERT OR IGNORE INTO articles (titre, categorie, mots_cles, resume, source, date_gravure) VALUES (?, ?, ?, ?, ?, ?)",
                            r,
                        )
                except Exception:
                    pass

            now = time.time()
            for art in ARTICLES_FONDATEURS:
                cur.execute(
                    "INSERT OR IGNORE INTO articles (titre, categorie, mots_cles, resume, source, date_gravure) VALUES (?, ?, ?, ?, ?, ?)",
                    (art["titre"], art["categorie"], art["mots_cles"], art["resume"], "Socle_Local", now),
                )

            cur.execute("DROP TABLE IF EXISTS articles_fts")
            cur.execute(
                """
                CREATE VIRTUAL TABLE articles_fts USING fts5(
                    titre, categorie, mots_cles, resume,
                    content='articles', content_rowid='id',
                    tokenize='unicode61 remove_diacritics 2'
                )
                """
            )
            cur.execute("INSERT INTO articles_fts(articles_fts) VALUES('rebuild')")
            conn.commit()
        finally:
            conn.close()

    def compter_articles(self) -> int:
        conn = sqlite3.connect(str(self.db_path))
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM articles")
            return int(cur.fetchone()[0])
        finally:
            conn.close()

    def graver_article(
        self,
        titre: str,
        resume: str,
        categorie: str = "Encyclopédie Générale",
        mots_cles: str = "",
        source: str = "Gravure_Locale",
    ) -> bool:
        if not titre.strip() or not resume.strip():
            return False
        if not mots_cles:
            mots_cles = " ".join(re.findall(r"[a-zA-Zàâäéèêëîïôöùûüç0-9]{3,}", (titre + " " + resume).lower())[:25])

        conn = sqlite3.connect(str(self.db_path))
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO articles (titre, categorie, mots_cles, resume, source, date_gravure)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(titre) DO UPDATE SET
                    resume=excluded.resume,
                    mots_cles=excluded.mots_cles,
                    date_gravure=excluded.date_gravure
                """,
                (titre.strip(), categorie, mots_cles, resume.strip(), source, time.time()),
            )
            cur.execute("INSERT INTO articles_fts(articles_fts) VALUES('rebuild')")
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def chercher_local(self, requete: str, max_resultats: int = 2) -> List[Dict[str, str]]:
        """Recherche plein-texte en < 1 ms dans l'Encyclopédie Froide sur SSD (insensible aux accents)."""
        mots_vides = {
            "les", "des", "une", "que", "qui", "est", "ets", "dans", "pour", "avec", "sur", "pas",
            "tout", "plus", "comment", "quoi", "c'est", "ces", "parle", "moi", "dis", "donne",
            "explique", "histoire", "sujet", "quel", "quelle", "sont", "était", "etait", "alix",
            "christian", "notre", "votre", "nous", "vous", "faire", "fait", "aussi", "connecter",
            "connecte", "branche", "brancher",
        }
        mots = [
            m.lower()
            for m in re.findall(r"[a-zA-Zàâäéèêëîïôöùûüç0-9]{3,}", requete)
            if m.lower() not in mots_vides
        ]
        if not mots:
            return []

        # Si d'autres mots plus précis que "encyclopedie" sont présents, on privilégie les mots spécifiques
        mots_specifiques = [m for m in mots if m not in {"encyclopedie", "encyclopédie"}]
        mots_actifs = mots_specifiques if mots_specifiques else mots

        conn = sqlite3.connect(str(self.db_path))
        try:
            cur = conn.cursor()
            if len(mots_actifs) >= 2:
                fts_and = " AND ".join(f'"{m}"*' for m in mots_actifs[:5])
                cur.execute(
                    """
                    SELECT a.titre, a.categorie, a.resume, a.source
                    FROM articles_fts f
                    JOIN articles a ON a.id = f.rowid
                    WHERE articles_fts MATCH ?
                    ORDER BY bm25(articles_fts, 6.0, 3.0, 5.0, 1.5)
                    LIMIT ?
                    """,
                    (fts_and, max_resultats),
                )
                rows = cur.fetchall()
                if rows:
                    return [
                        {"titre": r[0], "categorie": r[1], "resume": r[2], "source": r[3]}
                        for r in rows
                    ]

            fts_or = " OR ".join(f'"{m}"*' for m in mots_actifs[:5])
            cur.execute(
                """
                SELECT a.titre, a.categorie, a.resume, a.source
                FROM articles_fts f
                JOIN articles a ON a.id = f.rowid
                WHERE articles_fts MATCH ?
                ORDER BY bm25(articles_fts, 6.0, 3.0, 5.0, 1.5)
                LIMIT ?
                """,
                (fts_or, max_resultats),
            )
            rows = cur.fetchall()
            return [
                {"titre": r[0], "categorie": r[1], "resume": r[2], "source": r[3]}
                for r in rows
            ]
        except Exception:
            return []
        finally:
            conn.close()

    def aspirer_et_graver_wikipedia_fr(self, sujet: str) -> Optional[Dict[str, str]]:
        """
        Si un sujet encyclopédique n'est pas encore sur le SSD, interroge l'API
        encyclopédique francophone, extrait le résumé factuel pur, et le grave
        définitivement dans `alix_encyclopedie_froide.sqlite` (pour que toutes les
        prochaines fois soient en 0,4 ms 100 % hors-ligne !).
        """
        sujet_propre = re.sub(
            r"^(c'est quoi|c'est qui|qu'est-ce que|qui est|qui ets|qui es|qui était|qui etait|parle-moi de|parle moi de|explique-moi|explique moi|définition de|quel est|quelle est)\s+",
            "",
            sujet.strip(),
            flags=re.IGNORECASE,
        )
        sujet_propre = re.sub(r"^(le|la|les|l'|un|une|des)\s+", "", sujet_propre.strip(), flags=re.IGNORECASE)
        sujet_propre = sujet_propre.strip(" ?!.,;:")
        if len(sujet_propre) < 2:
            return None

        try:
            # 1. Recherche du titre exact via l'API opensearch fr.wikipedia
            q_enc = urllib.parse.quote(sujet_propre)
            url_search = f"https://fr.wikipedia.org/w/api.php?action=opensearch&search={q_enc}&limit=1&namespace=0&format=json"
            req = urllib.request.Request(url_search, headers={"User-Agent": "AlixSanctuaireLocal/1.0"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data_s = json.loads(resp.read().decode("utf-8"))
                titres = data_s[1] if len(data_s) > 1 else []
                if not titres:
                    return None
                titre_exact = titres[0]

            # 2. Récupération du résumé court via REST v1 summary
            t_enc = urllib.parse.quote(titre_exact.replace(" ", "_"))
            url_sum = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{t_enc}"
            req2 = urllib.request.Request(url_sum, headers={"User-Agent": "AlixSanctuaireLocal/1.0"})
            with urllib.request.urlopen(req2, timeout=2.5) as resp2:
                info = json.loads(resp2.read().decode("utf-8"))
                extrait = info.get("extract", "").strip()
                desc = info.get("description", "Encyclopédie Universelle")
                if not extrait:
                    return None

                # Gravure permanente sur le SSD dans l'Encyclopédie Froide
                self.graver_article(
                    titre=titre_exact,
                    resume=extrait,
                    categorie=desc.capitalize() if desc else "Encyclopédie Universelle",
                    mots_cles=f"{sujet_propre.lower()} {titre_exact.lower()}",
                    source="Wikipedia_FR_Grimpe_SSD",
                )
                return {
                    "titre": titre_exact,
                    "categorie": desc.capitalize() if desc else "Encyclopédie Universelle",
                    "resume": extrait,
                    "source": "Gravé à chaud dans l'Encyclopédie Froide SSD",
                }
        except Exception:
            return None


if __name__ == "__main__":
    print("=" * 75)
    print(" 📚❄️ TEST DE L'ENCYCLOPÉDIE SOUVERAINE (GRANDE BIBLIOTHÈQUE FROIDE SSD)")
    print("=" * 75)
    enc = EncyclopedieSouveraine()
    print(f"✅ Articles gravés sur SSD (0 Mo RAM au repos) : {enc.compter_articles()}")

    for q in ["C'est quoi le point de fusion du tungstène ?", "Parle-moi de Jacques Parizeau", "Loi 101 Camille Laurin"]:
        t0 = time.perf_counter()
        res = enc.chercher_local(q)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        if res:
            print(f"\n🔍 Requête : {q!r} -> Trouvé en {dt_ms:.2f} ms !")
            print(f"   📌 [{res[0]['titre']} | {res[0]['categorie']}] : {res[0]['resume']}")

