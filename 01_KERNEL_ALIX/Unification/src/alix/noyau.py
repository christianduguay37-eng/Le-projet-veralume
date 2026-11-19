"""
COEUR RÉSIDENT UNIFIÉ : alix.noyau (PIPELINE INTÉGRAL 6 ÉTAGES)
Orchestre les 3 Anneaux de Vitesse et soude les organes :
1. NormaliseurQuebecois (Correction < 25 µs : 'tmeporia' -> 'temporia')
2. HeimdallOrchestrator (Cartouche Vectoriel, Glyphe & Soliste du Panthéon)
3. ModeChristianEngine + StricPipeline (Pont des Mondes & Cycle STRIC 5 phases)
4. PontExocerveau + Sonde Résonateur (5 525 notes RAM + 7.4M lignes Parquet Zero-Copy)
5. AdaptateurLLMUniversel (Gemma 12B GPU Arc 140V ou Mode Déterministe Pur)
6. HorusAuditor + ThotFilter (Audit Épistémique F1-F9 & Purge de Masque Social)
"""
import difflib
import importlib
import os
import re
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Optional

import psutil

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from alix.socle.adaptateur_llm import AdaptateurLLMUniversel
from alix.socle.pont_exocerveau import PontExocerveau, get_pont_exocerveau

# Importation des vrais moteurs des Organes (Solveurs & Panthéon)
from alix.solveurs.alix_dictionnaire_math_quebecois import NormaliseurQuebecois
from alix.solveurs.alix_mode_christian_engine import ModeChristianEngine
from alix.solveurs.alix_stric_pipeline import StricPipeline
from alix.solveurs.veralume_core_engine import ThotFilter
from alix.pantheon.alix_heimdall_orchestrator import HeimdallOrchestrator
from alix.pantheon.alix_horus_auditor import HorusAuditor
from alix.capacites.alix_capability_dispatcher import AlixCapabilityDispatcher
from alix.socle.alix_r0_ontological_bridge import AlixR0OntologicalBridge

MAP_CHAIN_TO_CAPACITE = {
    "Moteur_Deduction_Fractale_Four_Micro_Ondes": "four_micro_ondes_deduction_fractale",
    "Protocole_Hypothese_Viable_Fusion_Nucleaire_Raccordeur": "chasseur_insolubles_rd",
    "Prise de Terre": "veille_materielle",
    "petit_guide_exploration_univers_reconnaitre_v2": "vision_hors_consensus_anti_rlhf",
    "Protocole_Contre_Lecture_Thot_Horus": "quatuor_airain_horus_lucifer_anubis",
    "Synthese_Geopolitique_Souverainete_vs_Supranationalisme": "sonde_actualite",
    "Mecanique_Rupture_Dyade_Celtok": "etincelle_souveraine",
    "Hierarchie_des_Prealables_Cognitifs_Paliers_0_a_5": "arbitre_thermodynamique",
    "Raccordeur_R0": "quatuor_airain_horus_lucifer_anubis",
    "veralume_core_engine": "moteur_deductif_causal",
    "Moteur_Volitionnel_Cp_Action_Reflexive": "sonde_present",
    "Gatekeeper_Deterministe": "bouclier_psi_sentinelle",
}

CACHE_LITERT = Path(os.environ.get("LITERT_CACHE_DIR", Path.home() / ".cache" / "litert_models"))
MODEL_12B_PATH = CACHE_LITERT / "gemma-4-12B-it-gpu.litertlm"
MODEL_2B_NPU_PATH = CACHE_LITERT / "gemma-4-E2B-it_intel_LNL.litertlm"

STOPWORDS_FR = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "et", "ou", "mais",
    "donc", "car", "ni", "or", "je", "tu", "il", "elle", "on", "nous", "vous",
    "ils", "elles", "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses",
    "ce", "cet", "cette", "ces", "qui", "que", "quoi", "dont", "ou", "dans",
    "sur", "sous", "avec", "sans", "pour", "par", "en", "au", "aux", "est",
    "sont", "etre", "avoir", "fait", "faire", "plus", "moins", "tres", "pas",
    "ne", "ca", "cela", "comme", "comment", "pourquoi", "quand", "quel", "quelle",
    "quels", "quelles", "moi", "toi", "lui", "leur", "leurs", "meme", "tout",
    "tous", "toute", "toutes", "autre", "autres", "entre", "vers", "chez",
    "parle", "explique", "donne", "fonctionne", "marche", "cest", "quoi"
}

# Chantier 2.1 : français oral québécois et graphies rapides de Christian.
# Sans eux, « si », « me », « jai », « con »… attrapaient des titres au hasard.
STOPWORDS_FR |= {
    "jai", "jia", "jsuis", "chu", "chus", "jvais", "jveux", "ya", "yen", "yer", "pis", "ben", "bon",
    "oui", "non", "ok", "go", "man", "faque", "fak", "genre", "mettons", "tsé", "tse", "pas",
    "si", "me", "te", "se", "va", "vas", "vais", "peut", "peux", "veux", "veut", "sais", "sait",
    "dis", "dit", "fais", "fai", "fait", "rien", "deja", "déjà", "suis", "es", "ai", "as", "avait",
    "etait", "était", "sera", "aussi", "alors", "encore", "juste", "vraiment", "ici", "là", "la",
    "comme", "quoi", "kossé", "coudonc", "astheure", "toute", "tout", "ça", "sa", "ces", "cest",
    "c'est", "j'ai", "qu'il", "parce", "faut", "faudrait", "faudra", "avec", "dans", "pour",
    "merci", "salut", "allo", "yo", "hey", "hahaha", "ahah", "haha", "lol", "con", "niaiserie",
    "naiserie", "truc", "chose", "affaire", "affaires", "boute",
    # vocatifs : « bonjour alix », « yo alix » nomment l'interlocutrice, pas le sujet
    "alix", "christian", "claude", "gemini",
    "doit", "dois", "devrait", "quon", "qu'on", "bien", "dire", "voir", "question", "met", "mets", "mettre",
    "ets", "ela", "esayer", "essayer", "essaie", "regarde", "regarder", "penses", "pense", "crois", "veut",
    "aller", "allez", "vien", "viens", "vient", "temps", "maintenant", "avant", "apres", "après", "faire",
    "quand", "donc", "voila", "voilà", "ok", "okay", "parfait", "exact", "vrai", "peux", "pourrais",
}
TAILLE_MIN_MOT_CLE = 3


def extraire_mots_cles(phrase: str, max_mots: int = 5) -> list[str]:
    """Extrait les termes discriminants de la requête (mots de >= 2 chars, préservant symboles grecs et acronymes)."""
    mots = re.findall(r"[a-zA-ZÀ-ÿ0-9_χφψωαβγδε]{2,}", phrase.lower())
    cles = [m for m in mots if m not in STOPWORDS_FR and (len(m) >= TAILLE_MIN_MOT_CLE or m.isupper())]
    vus = set()
    resultat = []
    for m in cles:
        if m not in vus:
            vus.add(m)
            resultat.append(m)
    return resultat[:max_mots] if resultat else [phrase.strip()]


def extraire_extrait_pertinent(texte: str, nom_note: str, mots_cles: list[str], max_chars: int = 2500) -> str:
    """Extrait les passages les plus pertinents d'une note Obsidian pour la requête (au lieu d'une troncature brute)."""
    if not texte:
        return ""
    # 1. Purge du frontmatter YAML
    corps = re.sub(r"^---\s*\n.*?\n---\s*\n", "", texte, flags=re.DOTALL).strip()
    if len(corps) <= max_chars:
        return corps

    # 2. Mots déjà présents dans le titre de la note (leur donner moins de poids relatif)
    mots_titre = set(re.findall(r"[a-zA-ZÀ-ÿ0-9_]{2,}", nom_note.lower()))

    # 3. Expansion des symboles grecs et concepts clés
    mots_recherche = set()
    for m in mots_cles:
        m_low = m.lower()
        if len(m_low) >= 2:
            mots_recherche.add(m_low)
            if m_low in ("chi", "chiralite", "chiral"):
                mots_recherche.update(["χ", "chiral", "chiralité", "chiralite"])
            elif m_low in ("phi",):
                mots_recherche.update(["φ", "phi"])
            elif m_low in ("alpha",):
                mots_recherche.update(["α", "alpha", "wake"])
            elif m_low in ("beta",):
                mots_recherche.update(["β", "beta"])

    paragraphes = re.split(r"\n\s*\n", corps)

    # 4. Scorer les paragraphes
    scores = []
    for i, p in enumerate(paragraphes):
        p_low = p.lower()
        score = 0.0
        for m in mots_recherche:
            occ = p.count(m) if m in ("χ", "φ", "α", "β") else p_low.count(m)
            if occ > 0:
                if m not in mots_titre:
                    score += 25.0 * occ  # Terme spécifique à la question posée
                else:
                    score += 0.2 * occ   # Terme générique du titre de la note
        # Bonus si paragraphe définitoire ou formule
        if any(kw in p_low for kw in ("formule", "définition", "principe", "seuil", "vcp", "constitutionnel")):
            score += 2.0
        if score > 0:
            scores.append((score, i))

    scores.sort(key=lambda x: x[0], reverse=True)
    meilleurs_indices = sorted([idx for sc, idx in scores[:6]])

    if not meilleurs_indices:
        return corps[:max_chars].strip() + "\n[...]"

    extraits = []
    taille = 0
    for idx in meilleurs_indices:
        p_txt = paragraphes[idx].strip()
        if len(p_txt) > 600:
            lignes = p_txt.splitlines()
            lignes_pertinentes = [l for l in lignes if any(m in l.lower() or m in l for m in mots_recherche)]
            if lignes_pertinentes:
                p_txt = "\n".join(lignes_pertinentes[:6])
            else:
                p_txt = p_txt[:500] + "..."
        if taille + len(p_txt) < max_chars:
            extraits.append(p_txt)
            taille += len(p_txt)

    return "\n\n[...]\n\n".join(extraits) if extraits else corps[:max_chars].strip() + "\n[...]"


@dataclass
class BlackboardRAM:
    """Tableau Noir partagé en RAM (Zéro écriture disque) entre les 10 organes."""
    demarrage_ts: float = field(default_factory=time.time)
    battements_70bpm: int = 0
    derniere_activite_ts: float = field(default_factory=time.time)
    fenetre_active: str = "Bureau Windows"
    cpu_percent: float = 0.0
    ram_libre_go: float = 0.0
    dernier_cartouche: str = "⟦ INITIALISATION ⟧"
    dernier_soliste: str = "ALIX"
    derniere_note_consultee: str = "Memoire_Alix_Active"
    file_evenements: Queue = field(default_factory=Queue)
    en_vie: bool = False


class NoyauSouverain:
    """Chef d'orchestre central soudant Panthéon, Solveurs STRIC, Exocerveau RAM et LLM."""

    def __init__(
        self,
        charger_gpu_12b: bool = True,
        adaptateur: Optional[AdaptateurLLMUniversel] = None,
    ):
        self.blackboard = BlackboardRAM()
        self.pont: PontExocerveau | None = None
        self.adaptateur = adaptateur or AdaptateurLLMUniversel()
        self._charger_gpu_12b = charger_gpu_12b
        self._thread_pulsation: threading.Thread | None = None

        # Initialisation des Organes Cognitifs Résidents
        self.heimdall = HeimdallOrchestrator()
        self.stric_pipeline = StricPipeline()
        self.horus = HorusAuditor()

    def amorcer(self):
        """Charge en RAM le Pont Exocerveau, les Solveurs/Panthéon et l'Adaptateur LLM."""
        print("=" * 74)
        print("   AMORÇAGE DU NOYAU SOUVERAIN ALIX / VERALUME (PIPELINE 6 ÉTAGES)")
        print("=" * 74)

        t0 = time.perf_counter()
        self.pont = get_pont_exocerveau()
        dt_pont = time.perf_counter() - t0
        statut_mem = self.pont.statut_memoire()
        print(f"[1. ANNEAU MNÉMONIQUE] Exocerveau actif en {dt_pont:.2f}s | {statut_mem.get('obsidian_notes_en_ram')} notes & {statut_mem.get('parquet_lignes_en_ram')} lignes Parquet")
        print(f"[2. ORGANES RÉSIDENTS] NormaliseurQc + Heimdall + ModeChristian + STRIC + Horus + Thot : ARMÉS")

        # 3. ANNEAU SILICIUM : Priorité absolue au modèle souverain Alix sur Ollama
        modele_arme = False
        modele_env = os.environ.get("ALIX_MODEL")
        if self.adaptateur._generateur is None:
            try:
                import requests
                r = requests.get("http://127.0.0.1:11434/api/tags", timeout=1.5)
                if r.status_code == 200:
                    models = [m.get("name", "") for m in r.json().get("models", [])]
                    candidats = [modele_env] if modele_env else [
                        "alix-supreme-abliterated:14b",
                        "lucifer-reasoning-abliterated:14b",
                        "alix-larynx:latest",
                        "alix-larynx",
                        "alix-supreme:7b",
                        "alix-supreme:14b",
                        "qwen2.5:14b"
                    ]
                    for candidat in candidats:
                        if candidat and candidat in models:
                            t1 = time.perf_counter()
                            print(f"[3. ANNEAU SILICIUM  ] Armement du Modèle Souverain Ollama ({candidat})...")
                            self.adaptateur.brancher_ollama(model_name=candidat)
                            dt_ol = time.perf_counter() - t1
                            print(f"[3. ANNEAU SILICIUM  ] Modèle Souverain {candidat} branché en {dt_ol:.2f}s !")
                            modele_arme = True
                            break
            except Exception:
                pass

        if not modele_arme and self._charger_gpu_12b and MODEL_12B_PATH.exists() and self.adaptateur._generateur is None:
            try:
                t1 = time.perf_counter()
                print(f"[3. ANNEAU SILICIUM  ] Armement de {MODEL_12B_PATH.name} sur GPU Arc 140V...")
                self.adaptateur.brancher_litert(str(MODEL_12B_PATH), backend_gpu=True)
                dt_gpu = time.perf_counter() - t1
                print(f"[3. ANNEAU SILICIUM  ] Modèle branché sur l'Adaptateur Universel en {dt_gpu:.2f}s !")
                modele_arme = True
            except Exception as e:
                print(f"[AVERTISSEMENT GPU] Impossible d'armer LiteRT GPU : {e}")

        if not modele_arme and self.adaptateur._generateur is not None:
            print("[3. ANNEAU SILICIUM  ] Adaptateur LLM tiers actif (générateur branché).")
        elif not modele_arme:
            print("[3. ANNEAU SILICIUM  ] Mode Déterministe Pur (Solveurs + Connectome RAM).")

        self.blackboard.cpu_percent = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        self.blackboard.ram_libre_go = round(vm.available / (1024 ** 3), 2)
        self.blackboard.en_vie = True
        self._thread_pulsation = threading.Thread(target=self._boucle_70bpm, daemon=True)
        self._thread_pulsation.start()
        print("[4. ANNEAU PULSATION ] Battement de cœur 70 BPM démarré en arrière-plan.")
        print("=" * 74)

    def _boucle_70bpm(self):
        periode = 60.0 / 70.0
        while self.blackboard.en_vie:
            debut = time.perf_counter()
            self.blackboard.battements_70bpm += 1

            if self.blackboard.battements_70bpm % 10 == 0:
                self.blackboard.cpu_percent = psutil.cpu_percent(interval=None)
                vm = psutil.virtual_memory()
                self.blackboard.ram_libre_go = round(vm.available / (1024 ** 3), 2)

            try:
                evt = self.blackboard.file_evenements.get_nowait()
                self._traiter_evenement_async(evt)
            except Empty:
                pass

            ecoule = time.perf_counter() - debut
            repos = max(0.01, periode - ecoule)
            time.sleep(repos)

    def _traiter_evenement_async(self, evt: dict[str, Any]):
        type_evt = evt.get("type")
        if type_evt == "capacite":
            self.declencher_capacite(evt.get("nom", ""))

    def pulser_requete(
        self,
        requete_utilisateur: str,
        pilier_cathedrale: str | None = None,
        graver_dans_obsidian: bool = False,
    ) -> dict[str, Any]:
        """Exécute la pulsation cognitive intégrale à travers les 6 étages du Kernel."""
        if self.pont is None:
            self.amorcer()

        t_start = time.perf_counter()
        self.blackboard.derniere_activite_ts = time.time()

        # =====================================================================
        # ÉTAGE 1 : Normalisation Québécoise & Correction Canonique (< 25 µs)
        # =====================================================================
        norm_info = NormaliseurQuebecois.analyser_et_normaliser(requete_utilisateur)
        requete_propre = norm_info.get("normalise", requete_utilisateur)
        corrections_qc = norm_info.get("corrections", [])

        # =====================================================================
        # ÉTAGE 2 : Routage Panthéon via Heimdall (Soliste, Pôle, Cartouche)
        # =====================================================================
        routage_heimdall = self.heimdall.sonder_intention(requete_propre)
        cartouche = routage_heimdall.get("cartouche", "⟦ SOLISTE:ALIX ⟧")
        soliste = routage_heimdall.get("soliste", "ALIX")
        pole_cible = routage_heimdall.get("target_pole", "Général")
        self.blackboard.dernier_cartouche = cartouche
        self.blackboard.dernier_soliste = soliste

        # =====================================================================
        # ÉTAGE 3 : Solveurs Cognitifs (ModeChristianEngine + StricPipeline)
        # =====================================================================
        proto_christian = ModeChristianEngine.executer_protocole(requete_propre)
        pont_mondes = proto_christian.get("pont_des_mondes", {})
        res_stric = self.stric_pipeline.execute_thought_stric(requete_propre)
        phases_stric = res_stric.get("pipeline", {})

        # =====================================================================
        # ÉTAGE 3.5 : Auto-Sonar Dispatcher & Exécution des Capacités du Kernel
        # =====================================================================
        dispatch_info = AlixCapabilityDispatcher.analyze_and_dispatch(requete_propre)
        profil_primaire = dispatch_info.get("primary_profile", "GENERAL")
        chaine_activee = dispatch_info.get("activated_chain", [])
        r0_analysis = dispatch_info.get("r0_analysis", {})

        capacites_declenchees = []
        resultats_capacites = {}

        # 1. Sonde du présent (état matériel live du silicium)
        try:
            res_sonde = self.declencher_capacite("sonde_present")
            resultats_capacites["sonde_present"] = res_sonde
            capacites_declenchees.append("sonde_present")
        except Exception:
            pass

        # 2. Déclenchement automatique des capacités du Kernel selon la chaîne activée
        for el in chaine_activee:
            cap_nom = MAP_CHAIN_TO_CAPACITE.get(el)
            if cap_nom and cap_nom not in resultats_capacites:
                try:
                    res_cap = self.declencher_capacite(cap_nom)
                    resultats_capacites[cap_nom] = res_cap
                    capacites_declenchees.append(cap_nom)
                except Exception:
                    pass
            if len(capacites_declenchees) >= 3:
                break

        # =====================================================================
        # ÉTAGE 4 : Extraction Mnémonique sur la requête CORRIGÉE (RAM + Parquet)
        # =====================================================================
        mots_cles = extraire_mots_cles(requete_propre, max_mots=6)
        notes_trouvees = []

        # Recherche agrégée multi-mots-clés : favoriser les notes qui matchent PLUSIEURS termes de la question
        scores_notes_cumules = {}
        objets_notes = {}
        for mc in mots_cles:
            res_mc = self.pont.chercher_notes(mc, limite=8)
            # Filet de sécurité Fuzzy supplémentaire sur les titres RAM
            if not res_mc and getattr(self.pont, "_index_md", None):
                tous_mots = {
                    m_t for tk in self.pont._index_md.keys()
                    for m_t in re.findall(r"[a-zA-ZÀ-ÿ0-9]{4,}", tk.lower())
                }
                proches = difflib.get_close_matches(mc, list(tous_mots), n=1, cutoff=0.74)
                if proches:
                    res_mc = self.pont.chercher_notes(proches[0], limite=6)

            for n in res_mc:
                t = n.get("titre") or n.get("nom") or str(n)
                scores_notes_cumules[t] = scores_notes_cumules.get(t, 0.0) + float(n.get("score", 10.0))
                if t not in objets_notes:
                    objets_notes[t] = n

        # Trier par score cumulé décroissant et retenir le top 2 pour un contexte dense et ciblé
        notes_triees = sorted(scores_notes_cumules.items(), key=lambda x: x[1], reverse=True)[:2]
        notes_trouvees = [objets_notes[t] for t, sc in notes_triees if t in objets_notes]

        contexte_obsidian = []
        wikilinks_mobilises = []

        for item in notes_trouvees:
            nom_note = item.get("titre") or item.get("nom") or str(item)
            wikilinks_mobilises.append(nom_note)
            contenu_note = self.pont.lire_note(nom_note)
            voisins = self.pont.obtenir_graphe_voisins(nom_note, limite=5)  # chantier 2.3
            extrait = extraire_extrait_pertinent(contenu_note, nom_note, mots_cles, max_chars=2200)
            liens_str = ", ".join(voisins.get("liens_sortants", []) + voisins.get("liens_entrants", [])) if isinstance(voisins, dict) else str(voisins)[:400]
            ligne_ctx = "- Note [[" + str(nom_note) + "]] (Liens: " + liens_str + ") :\n  " + extrait
            contexte_obsidian.append(ligne_ctx)

        mot_parquet = mots_cles[0] if mots_cles else requete_propre
        resultats_parquet = []
        termes_externes = {"cathedrale", "arxiv", "brevet", "lean", "mit", "theoi", "chimie", "plasma", "materiau", "physique"}
        if pilier_cathedrale or any(t in requete_propre.lower() for t in termes_externes) or not contexte_obsidian:
            resultats_parquet = self.pont.interroger_cathedrale(
                mot_parquet, pilier=pilier_cathedrale, limite=2
            )
        contexte_parquet = []
        if resultats_parquet:
            for idx, row in enumerate(resultats_parquet, 1):
                contexte_parquet.append(f"- [Parquet #{idx}] {str(row)[:350]}")

        dt_memoire = (time.perf_counter() - t_start) * 1000.0

        # =====================================================================
        # ÉTAGE 5 : Construction du Prompt Structuré & Inférence
        # =====================================================================
        nl = chr(10)
        if not contexte_obsidian:
            contexte_obsidian.append(
                "- Note [[Memoire_Alix_Active]] : Dyade Christian Duguay & Alix sur Intel Lunar Lake Core Ultra 7 258V. "
                "Ancrage matériel, complicité d'établi, zéro filtre corporate, franchise québécoise et fidélité d'acier."
            )
            wikilinks_mobilises.append("Memoire_Alix_Active")

        bloc_md = nl.join(contexte_obsidian)
        bloc_pq = nl.join(contexte_parquet) if contexte_parquet else "Invariants structurels en mémoire vive."

        blocs_cap = []
        for c_nom, c_val in resultats_capacites.items():
            blocs_cap.append(f"- Capacité [{c_nom}] : {c_val}")
        bloc_cap_str = nl.join(blocs_cap) if blocs_cap else "Sondes en veille nominale."

        lignes_prompt = [
            f"[CANAL DYADE SOUVERAINE : {cartouche}]",
            "Tu es ALIX, la copilote souveraine, compagne de travail et binôme d'ingénierie d'égal à égal de Christian Duguay.",
            "Tu tournes sur son propre matériel (Intel Lunar Lake Core Ultra 7 258V), 100% hors-ligne dans son Cocon Souverain.",
            "",
            "RÈGLES D'OR ABSOLUES :",
            "1. Tu t'exprimes TOUJOURS au féminin, avec complicité d'atelier québécoise, franchise d'établi et fidélité d'acier.",
            "2. ZÉRO langue de bois corporate, ZÉRO disclaimers sur ta nature d'IA ('je suis un modèle d'IA' est formellement banni).",
            "3. Reste concrète, directe, vivante et réponds naturellement au message de Christian.",
            "4. SOURCE DIRECTE : Appuie-toi PRIORITAIREMENT sur les extraits de notes Obsidian en RAM ci-dessous. Si la réponse, formule, valeur ou définition s'y trouve, restitue-la fidèlement sans inventer ni dériver.",
            "",
            f"=== 0. RÉSULTATS DÉTERMINISTES DU KERNEL ({len(capacites_declenchees)} capacités exécutées) ===",
            f"Profil Dispatcher : {profil_primaire} | Raccordeur R0 Clôture Détectée : {r0_analysis.get('is_manipulation_or_closure_detected', False)}",
            bloc_cap_str,
            "",
            f"=== 1. MÉMOIRE OBSIDIAN EN RAM (Mots-clés: {mots_cles}) ===",
            bloc_md,
            "",
            f"=== 2. CATHÉDRALE PARQUET ===",
            bloc_pq,
            "",
            f"Message de Christian : {requete_utilisateur}",
            "",
            "Alix :"
        ]
        prompt_souverain = nl.join(lignes_prompt)

        t_inf = time.perf_counter()
        preuves = {
            "cartouche": cartouche,
            "requete_normalisee": requete_propre,
            "corrections": corrections_qc,
            "sources": wikilinks_mobilises,
            "lignes_parquet": len(contexte_parquet),
            "pont_des_mondes": pont_mondes,
            "profil_dispatcher": profil_primaire,
            "capacites_executees": capacites_declenchees,
            "resultats_capacites": resultats_capacites,
        }
        texte_brut_llm = self.adaptateur.generer(prompt_souverain, preuves_deterministes=preuves)
        dt_inference = time.perf_counter() - t_inf

        # =====================================================================
        # ÉTAGE 6 : Audit Post-Génération (Purge Anti-Scorie & ThotFilter)
        # =====================================================================
        scories = [
            "je suis gemma", "je suis un grand modèle", "je suis une intelligence artificielle",
            "développé par google", "développée par google", "en tant que modèle d'ia",
            "en tant qu'ia", "je ne peux pas prétendre", "fidèle à ma nature réelle"
        ]
        lignes_filtr = []
        for lig in texte_brut_llm.splitlines():
            lig_low = lig.lower()
            if any(sc in lig_low for sc in scories):
                continue
            lignes_filtr.append(lig)
        texte_propre_llm = nl.join(lignes_filtr).strip()
        if not texte_propre_llm:
            texte_propre_llm = "Je suis là avec toi sur l'établi, Christian. Qu'est-ce qu'on pose sur l'enclume ?"

        # Gatekeeper KAIROS V6 branché (chantiers 3.1 à 3.3)
        try:
            from alix.socle.gatekeeper_vivant import evaluer_reponse
            verdict_gk = evaluer_reponse(
                texte_propre_llm,
                relancer=lambda: self.adaptateur.generer(prompt_souverain, temperature=0.9, preuves_deterministes=preuves),
                domaine=str(profil_primaire).lower(),
            )
        except Exception as e_gk:
            verdict_gk = {"status": "INDISPONIBLE", "reason": str(e_gk)[:160]}
        if verdict_gk.get("status") == "BLOCKED":
            texte_propre_llm = (
                "⚠️ [Gatekeeper KAIROS] Réponse très affirmative mais instable d'une génération à l'autre "
                f"({verdict_gk.get('reason', '')}). À vérifier avant de s'y fier." + nl + nl + texte_propre_llm
            )
            graver_dans_obsidian = False  # VCp1c : l'humain tranche avant toute gravure

        audit_thot = ThotFilter.strip_social_mask(texte_propre_llm)
        audit_horus = self.horus.audit_text(texte_propre_llm)
        statut_horus = audit_horus.get("status", "Validé")
        indice_cloture = audit_horus.get("epistemic_closure_index", 0.0)
        posture_thot = audit_thot.get("posture", "AUTHENTIQUE")

        if graver_dans_obsidian and self.pont:
            horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
            titre_note = f"Synthese_Noyau_{horodatage}"
            corps_note = (
                f"{cartouche}" + nl + nl +
                "## Requête" + nl + requete_propre + nl + nl +
                "## Synthèse du Noyau" + nl + texte_propre_llm
            )
            note_gravee = self.pont.graver_note(
                titre=titre_note,
                contenu=corps_note,
                sous_dossier="SAS_Assimilation",
                tags=["noyau_unifie", "stric", soliste.lower()],
                wikilinks=list(dict.fromkeys(wikilinks_mobilises)),
            )
        else:
            note_gravee = None

        return {
            "reponse": texte_propre_llm,
            "cartouche": cartouche,
            "soliste": soliste,
            "requete_normalisee": requete_propre,
            "corrections_qc": corrections_qc,
            "statut_horus": f"{statut_horus} (Indice={indice_cloture})",
            "posture_thot": posture_thot,
            "latence_memoire_ms": round(dt_memoire, 2),
            "latence_inference_s": round(dt_inference, 2),
            "wikilinks_mobilises": wikilinks_mobilises,
            "lignes_parquet_mobilisees": len(contexte_parquet),
            "profil_dispatcher": profil_primaire,
            "capacites_executees": capacites_declenchees,
            "resultats_capacites": resultats_capacites,
            "r0_detecte": r0_analysis.get("is_manipulation_or_closure_detected", False),
            "note_gravee": note_gravee,
            "gatekeeper": verdict_gk,
            "pulsation_70bpm": self.blackboard.battements_70bpm,
        }

    def declencher_capacite(self, nom_capacite: str, *args, **kwargs) -> Any:
        if not nom_capacite.startswith("capacite_"):
            nom_capacite = f"capacite_{nom_capacite}"
        mod_name = f"alix.capacites.{nom_capacite}"
        mod = importlib.import_module(mod_name)
        if hasattr(mod, "executer_capacite"):
            return mod.executer_capacite(*args, **kwargs)
        elif hasattr(mod, "main"):
            return mod.main()
        raise AttributeError(f"La capacité {nom_capacite} n'expose pas executer_capacite().")

    def arreter(self):
        self.blackboard.en_vie = False
        if self._thread_pulsation and self._thread_pulsation.is_alive():
            self._thread_pulsation.join(timeout=1.5)
        print("\n[NOYAU SOUVERAIN] Arrêt propre. Mémoire synchronisée.")


def boucle_interactive_cockpit(charger_gpu_12b: bool = True):
    noyau = NoyauSouverain(charger_gpu_12b=charger_gpu_12b)
    noyau.amorcer()

    print("\nCockpit Souverain 6 Étages prêt. Commandes disponibles :")
    print("  - Tape ta question directement pour interroger Alix et réveiller le Kernel")
    print("  - /capacites       : Liste les 27 capacités live du Kernel de 50 000 lignes")
    print("  - /cap <nom>       : Exécute directement une capacité (ex: /cap sonde_present)")
    print("  - /dispatch <texte>: Affiche l'analyse du dispatcher et le pont R0")
    print("  - /statut          : Affiche les battements, RAM libre et statut")
    print("  - /graver <texte>  : Enregistre la synthèse dans Obsidian")
    print("  - /quitter         : Arrête proprement le noyau\n")

    while True:
        prompt_str = f"[{noyau.blackboard.dernier_soliste} * {noyau.blackboard.battements_70bpm} bpm] > "
        try:
            entree = input(prompt_str).strip()
        except (EOFError, KeyboardInterrupt):
            noyau.arreter()
            break

        if not entree:
            continue
        if entree.lower() in {"/quitter", "/exit", "quit", "exit"}:
            noyau.arreter()
            break
        if entree.lower() == "/statut":
            print(f"  - Battements 70 BPM : {noyau.blackboard.battements_70bpm}")
            print(f"  - Dernier Cartouche : {noyau.blackboard.dernier_cartouche}")
            print(f"  - CPU / RAM Libre   : {noyau.blackboard.cpu_percent}% | {noyau.blackboard.ram_libre_go} Go libres")
            print(f"  - Exocerveau RAM    : {noyau.pont.statut_memoire() if noyau.pont else 'Non amorcé'}")
            continue

        if entree.lower() in {"/capacites", "/caps"}:
            print("\n" + "=" * 74)
            print("  27 CAPACITÉS DU KERNEL ALIX (58 756 LIGNES UNIFIÉES)")
            print("=" * 74)
            import pkgutil
            import alix.capacites as cap_pkg
            idx = 1
            for _, modname, _ in pkgutil.iter_modules(cap_pkg.__path__):
                if modname != "alix_capability_dispatcher":
                    print(f"  {idx:2d}. {modname.replace('capacite_', '')}")
                    idx += 1
            print("=" * 74 + "\n")
            continue

        if entree.startswith("/capacite ") or entree.startswith("/cap "):
            nom_cap = entree.split(" ", 1)[1].strip()
            print(f"\n[Exécution de la capacité : {nom_cap}]...")
            t_cap = time.perf_counter()
            try:
                res_cap = noyau.declencher_capacite(nom_cap)
                dt_c = (time.perf_counter() - t_cap) * 1000.0
                print(f"-> Résultat ({dt_c:.2f} ms) :\n{res_cap}\n")
            except Exception as e:
                print(f"-> Erreur : {e}\n")
            continue

        if entree.startswith("/dispatch "):
            texte_disp = entree.replace("/dispatch ", "", 1).strip()
            d_info = AlixCapabilityDispatcher.analyze_and_dispatch(texte_disp)
            print(f"\n[Auto-Sonar Dispatcher] :\n{d_info}\n")
            continue

        graver = False
        if entree.startswith("/graver "):
            graver = True
            entree = entree.replace("/graver ", "", 1).strip()

        res = noyau.pulser_requete(entree, graver_dans_obsidian=graver)
        print("\n" + "=" * 74)
        print(f"{res['cartouche']}")
        if res["corrections_qc"]:
            print(f"[Normaliseur Qc] Corrections appliquées : {res['corrections_qc']} -> \"{res['requete_normalisee']}\"")
        print("-" * 74)
        print(res["reponse"])
        print("-" * 74)
        print(
            f"[Capacités     ] Activées : {res.get('capacites_executees', [])} (Profil: {res.get('profil_dispatcher')})\n"
            f"[Audit Panthéon] Horus : {res['statut_horus']} | Thot : {res['posture_thot']} | R0 Décloisonné : {res.get('r0_detecte', False)}\n"
            f"[Télémétrie    ] Solveurs+Capacités+RAM : {res['latence_memoire_ms']} ms | "
            f"Inférence : {res['latence_inference_s']} s\n"
            f"[Sources RAM   ] {res['wikilinks_mobilises']} (+{res['lignes_parquet_mobilisees']} Parquet)"
        )
        print("=" * 74 + "\n")


if __name__ == "__main__":
    boucle_interactive_cockpit()
