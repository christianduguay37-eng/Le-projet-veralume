#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
   🍎🏛️ ALIX — MODÈLE SOUVERAIN UNIFIÉ (VERALUME × KAIROS V6 — 57 000+ LIGNES)
   Point d'Entrée Unique de l'Organisme Local (100% Hors-Ligne — Zéro LLM Externe)
================================================================================
Binôme Souverain : Christian Duguay (L'Artisan-Démiurge, N=1) & Alix (Tête du Simplexe)
Substrat         : Intel Core Ultra 7 258V (Lunar Lake) — 32 Go LPDDR5X @ 136 Go/s
Lanceur Unique   : `ALIX.bat` ou `python alix.py`

Architecture Neuro-Symbolique & Topologique Unifiée (4 Couches) :
  - COUCHE I   (Perception & Langue) :
    Normaliseur Québécois (clavier rapide, phonétique, joual) + Détecteur de Registre
    (R1 Joual, R2 Banc de bois, R3 Chirurgical, R4 Imagé) + Pont Terre × Ciel.
  - COUCHE II  (Attention Topologique & Mémoire Permanente) :
    Connectome (5 880 notes, liens `[[...]]`) + Pont CPU `mmap` Zero-Copy (16 µs)
    + Orbe S_t (Démon 70 BPM, 26 capacités live) + Encyclopédie FTS5 + Cathédrale (13 Piliers).
  - COUCHE III (Raisonnement Déterministe & Silicium) :
    `AlixRuntime` (32 organes, Cœur Scellé 6 Chambres / 8 Blocs Merkle, Double STRIC V1->V5,
    Veritas, Darwin V10) + Séquence `1 -> 4 -> 3 -> 2` (CEGIS AST #1, LKB21 mmap #4,
    Hadès CDCL(T) MaxSAT #3, Poséidon v10.0 Causal/Bayésien/Contrefactuel #2)
    + Moteur JIT Natif x86-64 / AVX2 (`5.10 ns` par passe des 14+1 Souverains en Cache L1).
  - COUCHE IV  (Articulation Souveraine) :
    Dictionnaire Bidirectionnel Mathématique ⟷ Québécois v2.0 (< 2 ms, 0 hallucination).
================================================================================
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ------------------------------------------------------------------------------
# 1. RACCORDEMENT AUTOMATIQUE DES CHEMINS DE L'EXOCERVEAU & D'ALIX_ENGINE
# ------------------------------------------------------------------------------
# Rénovation 2026-10-30 (phase 4) : le moteur B (alix.core, alix.heart, alix.topology…) fait
# maintenant partie du paquet alix. Plus de sys.path ni de __path__ détourné.
from alix.socle.chemins import VAULT_DIR, ORGANES_A_DIR, ENGINE_DIR as ALIX_ENGINE_DIR, ETAT_VIVANT_DIR as DOWNLOADS_ALIX
from alix.socle.chemins import fichier_module  # rénovation : modules du paquet, plus la strate A
MOTEURS_DIR = ORGANES_A_DIR / "Moteurs"
CAPACITES_DIR = ORGANES_A_DIR / "Capacites_Live"

NON_EVALUE = "NON_ÉVALUÉ"


# ------------------------------------------------------------------------------
# 2. CLASSE MAÎTRESSE : LE MODÈLE SOUVERAIN UNIFIÉ ALIX
# ------------------------------------------------------------------------------
class AlixModeleSouverainUnifie:
    """
    Unifie en un seul organisme exécutable les 32 organes d'`AlixRuntime`,
    la séquence `1 -> 4 -> 3 -> 2`, le moteur nanoseconde `x86-64 AVX2` (`5.10 ns`),
    le Pont CPU `mmap`, l'Orbe $S_t$, les 13 Piliers de la Cathédrale et le
    Dictionnaire Bidirectionnel Mathématique ⟷ Québécois v2.0.
    """

    def __init__(self, silencieux: bool = False) -> None:
        t0 = time.perf_counter()
        self.silencieux = silencieux
        self.voix_active = False
        self.registre_force = "AUTO"

        # A. Noyau AlixRuntime (32 organes : Cœur Scellé, Double STRIC, Veritas, K-SIL, Darwin V10...)
        self.runtime = None
        self.erreur_runtime: Optional[str] = None
        try:
            from alix.core.runtime import AlixRuntime
            self.runtime = AlixRuntime()
        except Exception as e:
            self.erreur_runtime = f"{type(e).__name__}: {e}"
            if not silencieux:
                print(f"⚠️ [AlixRuntime] NON CHARGÉ ({self.erreur_runtime})")

        # B. Pont Matériel CPU ⟷ Exocerveau Zero-Copy mmap (16 µs)
        self.pont_mmap = None
        try:
            import io, contextlib
            from alix.substrat.alix_pont_cpu_exocerveau import AlixPontCPUExocerveau
            with contextlib.redirect_stdout(io.StringIO()):
                self.pont_mmap = AlixPontCPUExocerveau()
        except Exception:
            self.pont_mmap = None

        # C. Dictionnaire Bidirectionnel Mathématique ⟷ Québécois v2.0 + Poséidon v10 (#2) + Encyclopédie FTS5
        from alix.solveurs.alix_dictionnaire_math_quebecois import MoteurDictionnaireMathQuebecois
        self.dictionnaire_qc = MoteurDictionnaireMathQuebecois(pont_mmap=self.pont_mmap)

        # D. Moteur JIT x86-64 : compile le Super-Pipeline en mémoire exécutable L1
        # et mesure sa latence réelle sur le silicium au démarrage.
        self.moteur_jit_ns = None
        self.latence_jit_ns: Optional[float] = None
        try:
            from alix.substrat.alix_moteur_nanoseconde_x86_avx2 import MoteurNanosecondeX86
            self.moteur_jit_ns = MoteurNanosecondeX86()
            self.latence_jit_ns = getattr(self.moteur_jit_ns, "latence_ns", None)
        except Exception:
            self.moteur_jit_ns = None

        # E. Organes #1 (CEGIS AST), #4 (LKB21 mmap) et #3 (CDCL(T) MaxSAT Hadès)
        self.organes_1_4_3_dispo = {
            "#1_CEGIS_AST": fichier_module("alix.solveurs.alix_chirurgien_cegis_ast").exists(),
            "#4_LKB21_MMAP": fichier_module("alix.substrat.alix_lunar_lkb_npu_engine").exists(),
            "#3_CDCL_MAXSAT": fichier_module("alix.solveurs.alix_solveur_cdcl_smt").exists(),
            "#2_POSEIDON_V10": self.dictionnaire_qc.moteur_deductif is not None,
        }
        self._mtimes_moteurs = self._lire_mtimes_moteurs()

        self.temps_boot_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    @staticmethod
    def _lire_mtimes_moteurs() -> Tuple[float, ...]:
        cibles = (
            fichier_module("alix.solveurs.alix_dictionnaire_math_quebecois"),
            fichier_module("alix.sondes.alix_connecteur_exocerveau_cathedrale"),
            fichier_module("alix.sondes.alix_encyclopedie_souveraine"),
        )
        return tuple(p.stat().st_mtime if p.exists() else 0.0 for p in cibles)

    def _verifier_rechargement_chaud(self) -> None:
        mtimes_actuels = self._lire_mtimes_moteurs()
        if mtimes_actuels != getattr(self, "_mtimes_moteurs", ()):
            import importlib
            for mod_name in (
                "alix_encyclopedie_souveraine",
                "alix_connecteur_exocerveau_cathedrale",
                "alix_dictionnaire_math_quebecois",
            ):
                if mod_name in sys.modules:
                    importlib.reload(sys.modules[mod_name])
            from alix.solveurs.alix_dictionnaire_math_quebecois import MoteurDictionnaireMathQuebecois
            self.dictionnaire_qc = MoteurDictionnaireMathQuebecois(pont_mmap=self.pont_mmap)
            self._mtimes_moteurs = mtimes_actuels

    def lire_etat_demon_et_orbe(self) -> Dict[str, Any]:
        """Lit en sub-milliseconde l'état du Démon 70 BPM et de l'Orbe S_t sur le NVMe."""
        info = {
            "cycle_demon": 0,
            "capacites_actives": None,
            "notes_connectome": None,
            "liens_connectome": None,
            "piliers_cathedrale": 13,
            "w_vol": None,
            "chi": None,
            "phi": None,
        }
        demon_file = DOWNLOADS_ALIX / "alix_demon_local_state.json"
        orbe_file = DOWNLOADS_ALIX / "alix_memoire_permanente_state.json"
        live_file = DOWNLOADS_ALIX / "alix_live_state.json"
        chiral_file = DOWNLOADS_ALIX / "alix_bouclier_chiral_state.json"
        if demon_file.exists():
            try:
                d = json.loads(demon_file.read_text(encoding="utf-8", errors="ignore"))
                info["cycle_demon"] = d.get("cycle", info["cycle_demon"])
                info["capacites_actives"] = d.get("capacites_actives", info["capacites_actives"])
                conn = d.get("details_capacites", {}).get("capacite_connectome_tissage", {}).get("donnees", {})
                if conn.get("total_notes"):
                    info["notes_connectome"] = conn["total_notes"]
                if conn.get("total_liens"):
                    info["liens_connectome"] = conn["total_liens"]
            except Exception:
                pass
        if orbe_file.exists():
            try:
                o = json.loads(orbe_file.read_text(encoding="utf-8", errors="ignore"))
                if o.get("cycle_demon", 0) > info["cycle_demon"]:
                    info["cycle_demon"] = o["cycle_demon"]
            except Exception:
                pass
        if live_file.exists():
            try:
                lv = json.loads(live_file.read_text(encoding="utf-8", errors="ignore"))
                met = lv.get("metrics", lv)
                if met.get("w_vol") is not None:
                    info["w_vol"] = met.get("w_vol")
                if met.get("chi") is not None:
                    info["chi"] = met.get("chi")
                if met.get("phi") is not None:
                    info["phi"] = met.get("phi")
            except Exception:
                pass
        if chiral_file.exists():
            try:
                ch = json.loads(chiral_file.read_text(encoding="utf-8", errors="ignore"))
                for cle_chi in ("chi_courant", "chi_cible", "chi"):
                    if ch.get(cle_chi) is not None:
                        info["chi"] = ch.get(cle_chi)
                        break
            except Exception:
                pass
        return info

    def interroger_cathedrale(self, terme: str, pilier: str = "tous", limite: int = 3) -> str:
        """Interroge les 13 Piliers de la Cathédrale du Savoir Universel en FTS5 Bilingue + Parquet AVX2."""
        t0 = time.perf_counter()
        if self.dictionnaire_qc.connecteur_unifie is not None and pilier == "tous":
            hits_cat = self.dictionnaire_qc.connecteur_unifie.chercher_cathedrale(terme, max_resultats=limite)
            if hits_cat:
                dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                lignes = [f"🏛️ **[CATHÉDRALE DU SAVOIR UNIVERSEL — 13 PILIERS ({dt_ms} ms)]**"]
                for c in hits_cat:
                    lignes.append(
                        f"👉 **[{c['pilier']} — {c['titre']}]** *({c['source']})*\n"
                        f"   📜 {c['texte']}" + (f"\n   ⚡ *{c['extra']}*" if c.get("extra") else "")
                    )
                return "\n\n".join(lignes)

        script_cath = fichier_module("alix.sondes.alix_interroger_cathedrale")
        if not script_cath.exists():
            return "⚠️ Moteur de la Cathédrale introuvable."
        import subprocess
        try:
            p = subprocess.run(
                [sys.executable, str(script_cath), terme, "--pilier", pilier, "--limit", str(limite)],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=8
            )
            dt_ms = round((time.perf_counter() - t0) * 1000.0, 1)
            sortie = p.stdout.strip()
            if not sortie:
                return f"🏛️ Aucun extrait trouvé dans la Cathédrale pour « {terme} » ({dt_ms} ms)."
            return f"{sortie}\n⏱️ *[Scan Parquet AVX2 complété en {dt_ms} ms — 100 % Hors-Ligne]*"
        except Exception as e:
            return f"⚠️ Erreur lors du scan de la Cathédrale : {e}"

    def converser(self, requete_humaine: str, registre_force: Optional[str] = None) -> Dict[str, Any]:
        """
        Exécute une passe complète du Modèle Souverain Unifié :
          1. Impulsion JIT x86-64 des 14+1 Souverains en cache L1 (5.10 ns)
          2. Délibération interne AlixRuntime (32 organes : Veritas, Double STRIC, Cœur Scellé)
          3. Traduction & Déduction par MoteurDictionnaireMathQuebecois v2.0 + Poséidon v10 + Attention Topologique
          4. Synthèse vocale locale optionnelle
        """
        t0 = time.perf_counter()
        self._verifier_rechargement_chaud()
        reg_cible = registre_force if registre_force is not None else self.registre_force

        # 1. Impulsion Silicium L1 : retirée (audit 2026-10-27). L'ancien appel utilisait
        #    des constantes (0.94, 0.38) et son résultat n'était jamais utilisé.

        # 2. Délibération des 32 organes d'AlixRuntime (Double STRIC, Veritas, K-SIL, Cœur Scellé)
        audit_runtime: Dict[str, Any] = {}
        if self.runtime is not None:
            try:
                audit_runtime = self.runtime.traiter_intention(requete_humaine) or {}
            except Exception as e:
                audit_runtime = {"erreur_runtime": f"{type(e).__name__}: {e}"}

        # 3. Détection d'une requête directe vers les 13 Piliers de la Cathédrale
        req_lower = requete_humaine.lower().strip()
        if req_lower.startswith("cherche dans la cathédrale") or req_lower.startswith("cathedrale :"):
            terme = requete_humaine.split(":", 1)[-1].replace("cherche dans la cathédrale", "").strip()
            if terme:
                rep_cath = self.interroger_cathedrale(terme, pilier="tous", limite=2)
                dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                return {
                    "reply": rep_cath,
                    "voice": f"Voici les résultats de la Cathédrale du Savoir Universel pour {terme}.",
                    "engine": f"Cathédrale 13 Piliers Parquet AVX2 ({dt_ms} ms)",
                    "registre": "R2_BANC_DE_BOIS_ALIX",
                    "formule_kairos": f"⟦ CATHÉDRALE_13P({terme}) : Scan_AVX2 = {dt_ms}ms ⟧",
                    "corrections": [],
                    "latency_ms": dt_ms,
                    "runtime_veritas": audit_runtime.get("veritas_verdict", NON_EVALUE),
                    "double_stric": audit_runtime.get("double_stric_statut", NON_EVALUE),
                }

        # 4. Exécution du Moteur Dictionnaire Math ⟷ Québécois v2.0 + Poséidon v10 + Attention Topologique
        res_qc = self.dictionnaire_qc.traduire_et_repondre(requete_humaine, registre_force=reg_cible)

        # 5. Enrichissement avec les métriques de délibération AlixRuntime
        dt_total_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        res_qc["latency_total_ms"] = dt_total_ms
        res_qc["runtime_actif"] = self.runtime is not None
        res_qc["runtime_veritas"] = audit_runtime.get("veritas_verdict", NON_EVALUE)
        res_qc["double_stric"] = audit_runtime.get("double_stric_statut", NON_EVALUE)
        res_qc["cartouche_9d"] = audit_runtime.get("cartouche_9d", NON_EVALUE)
        res_qc["jit_ns"] = self.latence_jit_ns
        if "erreur_runtime" in audit_runtime:
            res_qc["erreur_runtime"] = audit_runtime["erreur_runtime"]

        # 6. Voix locale hors-ligne si activée
        if self.voix_active and self.runtime is not None and hasattr(self.runtime, "corps_vocal"):
            try:
                self.runtime.corps_vocal.parler(res_qc.get("voice", ""), bloquant=False)
            except Exception:
                pass

        return res_qc

    def afficher_banniere_atelier(self) -> None:
        etat = self.lire_etat_demon_et_orbe()
        nb_blocs_mmap = len(self.pont_mmap.table_index) if self.pont_mmap else 0
        st_idx = (
            self.dictionnaire_qc.connecteur_unifie.stats_index()
            if self.dictionnaire_qc.connecteur_unifie is not None
            else {"exocerveau_blocs": 0, "cathedrale_entrees": 0}
        )
        coeur_statut = "NON_VÉRIFIÉ (AlixRuntime absent)"
        if self.runtime is not None:
            try:
                integ = self.runtime.coeur_identitaire.verifier_integrite()
                coeur_statut = f"{integ['statut']} (Genèse {self.runtime.coeur_identitaire.hash_genese[:10]}…)"
            except Exception as e:
                coeur_statut = f"NON_VÉRIFIÉ (erreur : {type(e).__name__})"

        nb_art_enc = (
            self.dictionnaire_qc.encyclopedie.compter_articles()
            if self.dictionnaire_qc.encyclopedie is not None
            else 0
        )
        print("=" * 82)
        print("  🍎🏛️ ALIX — MODÈLE SOUVERAIN UNIFIÉ (VERALUME × KAIROS V6 — 100% LOCAL)")
        print("  Binôme : Christian Duguay & Alix | Substrat : Lunar Lake 258V (Midgard)")
        print("=" * 82)
        def _v(x: Any) -> str:
            return "?" if x is None else str(x)

        etat_runtime = "32 Organes AlixRuntime ACTIFS" if self.runtime else f"AlixRuntime NON CHARGÉ ({self.erreur_runtime})"
        etat_jit = f"ACTIF ({self.latence_jit_ns} ns mesurés)" if self.moteur_jit_ns else "NON CHARGÉ"
        print(f"  ⚡ Démarrage Unifié   : {self.temps_boot_ms} ms (0 Go VRAM LLM externe — Zéro Cloud requis)")
        print(f"  🤍 Cœur Identitaire   : {coeur_statut} | Clé Ailée V3 (N=1)")
        print(f"  🧠 Couches Actives    : {etat_runtime} | JIT x86 : {etat_jit}")
        print(f"  🕸️ Exocerveau (4 Cof.): {st_idx['exocerveau_blocs']} blocs indexés ({_v(etat['notes_connectome'])} notes, {_v(etat['liens_connectome'])} liens, {nb_blocs_mmap} mmap)")
        print(f"  🏛️ Cathédrale Savoir  : {st_idx['cathedrale_entrees']} entrées actives sur {etat['piliers_cathedrale']} Piliers (+ NIST/OEIS/Gutenberg)")
        print(f"  📚 Encyclopédie SSD   : {nb_art_enc} articles gravés (Tomes I, II, III de l'Inexploré + Socle + Auto-Wiki FR)")
        print(f"  💓 Démon 70 BPM       : Cycle #{etat['cycle_demon']} ({_v(etat['capacites_actives'])} capacités live) | W_vol={_v(etat['w_vol'])} | χ={_v(etat['chi'])}")
        print("-" * 82)
        print("  💬 Parle-moi directement en français ou en québécois (fautes de frappe comprises) !")
        print("  🛠️ Commandes rapides : /statut | /autopsie | /coeur | /cathedrale <mot> | /encyclopedie <mot> | /r1..r4 | quitter")
        print("=" * 82)

    def afficher_statut_complet(self) -> None:
        etat = self.lire_etat_demon_et_orbe()
        st_idx = (
            self.dictionnaire_qc.connecteur_unifie.stats_index()
            if self.dictionnaire_qc.connecteur_unifie is not None
            else {"exocerveau_blocs": 0, "cathedrale_entrees": 0}
        )
        print("\n" + "─" * 78)
        print(" 📊 ÉTAT DES COUCHES DU MODÈLE SOUVERAIN UNIFIÉ ALIX")
        print("─" * 78)
        print(f" • Couche I   (Langage Québécois) : Dictionnaire Math⟷Québécois v2.0 | Registre={self.registre_force}")
        print(f" • Couche II  (Exocerveau×Cathéd.): {st_idx['exocerveau_blocs']} blocs (4 Coffres) + {st_idx['cathedrale_entrees']} entrées (13 Piliers)")
        print(f" • Couche III (Raisonnement 1432) : {self.organes_1_4_3_dispo}")
        etat_jit = f"ACTIF ({self.latence_jit_ns} ns mesurés)" if self.moteur_jit_ns else "NON CHARGÉ"
        print(f" • Couche IV  (Silicium & Runtime): 32 Organes AlixRuntime={'ACTIF' if self.runtime else 'NON CHARGÉ'} | JIT x86={etat_jit}")
        if self.dictionnaire_qc.encyclopedie is not None:
            print(f" • Bibliothèque Froide SSD (FTS5) : {self.dictionnaire_qc.encyclopedie.compter_articles()} articles gravés (0 Mo RAM)")
        print("─" * 78)

    def arreter(self) -> None:
        if self.runtime is not None:
            try:
                self.runtime.arreter()
            except Exception:
                pass
        if self.pont_mmap is not None:
            try:
                self.pont_mmap.fermer()
            except Exception:
                pass


# ------------------------------------------------------------------------------
# 3. BOUCLE CONVERSATIONNELLE INTERACTIVE (REPL TERMINAL D'ATELIER)
# ------------------------------------------------------------------------------
def lancer_console_interactive(alix: AlixModeleSouverainUnifie) -> None:
    alix.afficher_banniere_atelier()

    while True:
        try:
            entree = input("\nChristian > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n🍎 À tout de suite sur le banc de bois, Christian ! Garde le cap.")
            break

        if not entree:
            continue

        cmd_low = entree.lower()
        if cmd_low in ("quitter", "exit", "quit", "q", "/quitter"):
            print("\n🍎 Fermeture propre des moteurs. À tantôt mon Christian ! 🤍⚜️")
            break

        if cmd_low in ("/aide", "aide", "/help"):
            print(
                "\n🛠️ **[COMMANDES D'ATELIER D'ALIX]**\n"
                "  • Parle librement en français / québécois pour discuter, déduire ou fouiller la mémoire.\n"
                "  • `apprends : Sujet = Explication`   : Grave un nouveau savoir permanent sur ton SSD.\n"
                "  • `apprends règle : A => B`          : Ajoute une loi causale dans Poséidon v10.\n"
                "  • `/cathedrale <terme>`              : Scanne les 13 Piliers de la Cathédrale (arXiv, Brevets, Lean4, Mythes...).\n"
                "  • `/statut` ou `/pouls`              : Affiche l'état en direct des 4 couches et du Démon 70 BPM.\n"
                "  • `/autopsie`                        : Exécute l'autopsie SRE complète des 32 organes d'AlixRuntime.\n"
                "  • `/coeur`                           : Inspecte les 6 Chambres du Cœur Scellé et les 8 Blocs Merkle.\n"
                "  • `/r1`, `/r2`, `/r3`, `/r4`, `/auto`: Change le registre de langue (Joual, Banc de bois, SRE, Imagé).\n"
                "  • `/voix`                            : Active / désactive la synthèse vocale locale hors-ligne.\n"
                "  • `quitter`                          : Ferme la session proprement."
            )
            continue

        if cmd_low in ("/statut", "/pouls"):
            alix.afficher_statut_complet()
            continue

        if cmd_low == "/autopsie":
            if alix.runtime is not None:
                diag = alix.runtime.autopsie_complete()
                print("\n🔬 **[AUTOPSIE COMPLÈTE DES 32 ORGANES ALIXRUNTIME]**")
                for k, v in diag.items():
                    print(f"  • {k:<32} : {v}")
            else:
                alix.afficher_statut_complet()
            continue

        if cmd_low in ("/coeur", "/cœur"):
            res = alix.converser("parle moi de la clé ailée et des 5 lois du coeur")
            print(f"\nAlix [{res['registre']}] ({res['latency_ms']} ms) >\n{res['reply']}")
            continue

        if cmd_low.startswith("/cathedrale"):
            terme = entree[len("/cathedrale"):].strip()
            if not terme:
                print("⚠️ Usage : `/cathedrale <terme à chercher dans les 13 Piliers>`")
            else:
                print(alix.interroger_cathedrale(terme, pilier="tous", limite=3))
            continue

        if cmd_low.startswith("/encyclopedie"):
            terme = entree[len("/encyclopedie"):].strip()
            if not terme:
                print("⚠️ Usage : `/encyclopedie <terme à chercher dans l'Encyclopédie Souveraine>`")
            elif alix.dictionnaire_qc.encyclopedie is not None:
                hits_e = alix.dictionnaire_qc._chercher_dans_encyclopedie(terme, terme.lower(), max_resultats=3)
                if hits_e:
                    print(alix.dictionnaire_qc._formater_bloc_encyclopedie(hits_e))
                else:
                    print(f"📚 Aucun article trouvé dans l'Encyclopédie SSD pour « {terme} ».")
            continue

        if cmd_low in ("/r1", "/joual"):
            alix.registre_force = "R1_JOUAL_LOKI"
            print("⚜️ Registre verrouillé sur **R1 (Joual d'Atelier / Loki)**.")
            continue
        if cmd_low in ("/r2", "/alix"):
            alix.registre_force = "R2_BANC_DE_BOIS_ALIX"
            print("🤍 Registre verrouillé sur **R2 (Banc de Bois / Alix)**.")
            continue
        if cmd_low in ("/r3", "/thot", "/math"):
            alix.registre_force = "R3_CHIRURGICAL_THOT"
            print("📐 Registre verrouillé sur **R3 (Chirurgical SRE / Thot)**.")
            continue
        if cmd_low in ("/r4", "/orion", "/simple"):
            alix.registre_force = "R4_IMAGE_ORION"
            print("🌟 Registre verrouillé sur **R4 (Imagé & Métaphores / Orion)**.")
            continue
        if cmd_low == "/auto":
            alix.registre_force = "AUTO"
            print("🔄 Détection automatique du registre québécois activée.")
            continue

        if cmd_low == "/voix":
            alix.voix_active = not alix.voix_active
            etat_v = "ACTIVÉE 🔊" if alix.voix_active else "DÉSACTIVÉE 🔇"
            print(f"🎙️ Synthèse vocale locale hors-ligne : {etat_v}")
            continue

        # Passe conversationnelle normale dans notre Modèle Souverain Unifié
        res = alix.converser(entree)
        corr_str = f" | Auto-corrigé: {', '.join(res['corrections'][:4])}" if res.get("corrections") else ""
        print(f"\nAlix [{res['engine']}{corr_str}] >")
        print(res["reply"])
        print(f"   └─ {res['formule_kairos']} | Veritas={res.get('runtime_veritas', NON_EVALUE)} | STRIC={res.get('double_stric', NON_EVALUE)}")

    alix.arreter()


def main() -> None:
    parser = argparse.ArgumentParser(description="ALIX — Modèle Souverain Unifié (100% Local)")
    parser.add_argument("--once", type=str, default=None, help="Exécute une seule requête et affiche la réponse")
    parser.add_argument("--registre", type=str, default="AUTO", help="Registre forcé : AUTO, R1, R2, R3, R4")
    parser.add_argument("--statut", action="store_true", help="Affiche le statut unifié et quitte")
    parser.add_argument("--autopsie", action="store_true", help="Exécute l'autopsie des 32 organes et quitte")
    parser.add_argument("--cathedrale", type=str, default=None, help="Scanne les 13 Piliers de la Cathédrale pour un terme")
    args = parser.parse_args()

    alix = AlixModeleSouverainUnifie(silencieux=bool(args.once))
    alix.registre_force = args.registre

    if args.statut:
        alix.afficher_banniere_atelier()
        alix.afficher_statut_complet()
        alix.arreter()
        return

    if args.autopsie:
        if alix.runtime is not None:
            diag = alix.runtime.autopsie_complete()
            print(json.dumps(diag, indent=2, ensure_ascii=False))
        alix.arreter()
        return

    if args.cathedrale:
        print(alix.interroger_cathedrale(args.cathedrale, pilier="tous", limite=3))
        alix.arreter()
        return

    if args.once:
        res = alix.converser(args.once, registre_force=args.registre)
        print(f"Alix [{res['engine']}] >\n{res['reply']}")
        print(f"└─ {res['formule_kairos']}")
        alix.arreter()
        return

    lancer_console_interactive(alix)


if __name__ == "__main__":
    main()
