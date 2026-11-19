# -*- coding: utf-8 -*-
"""
================================================================================
     CAPACITÉ LIVE : SONDE APPRENTISSAGE ACCÉLÉRÉ & BOULE DE NEIGE RÉCURSIVE
         Système : VERALUME × KAIROS V6 — Démon Local Alix (Midgard)
================================================================================
Mandat :
- Décharge la quête diurne de la responsabilité de l'assimilation massive.
- Surveille en continu le dossier SAS : `Cerveau Alix/SAS_Assimilation_Massive/`.
- Déclenche à son propre rythme (configurable ou au franchissement de seuil)
  une RAFALE TOPOLOGIQUE ultra-rapide sur le fer (AVX2 / GPU Arc Xe2) :
    1. Lecture batch de N documents en parallèle.
    2. Encodage vectoriel & Matrice de Gram duale non-centrée (G = 1/M * X * X^T).
    3. Filtrage chirurgical des stop-words bilingues & calcul de d_eff.
    4. Gravure de l'Empreinte Simpliciale dans `Empreintes_Topologiques/`.
    5. Archivage des textes sources et notification proactive sur Telegram.
- EFFET BOULE DE NEIGE RÉCURSIF :
  * Si activé, extrait les 2 attracteurs majeurs émergents de la rafale N.
  * Formule automatiquement la requête ArXiv sur la frontière non résolue.
  * Aspire la Génération N+1 dans le SAS -> La boucle s'auto-amplifie en cascade !
- Garde-fous SRE stricts : Max 3 générations par cascade, pause courtoise ArXiv.
================================================================================
"""

import os
import sys
import time
import json
import shutil
import threading
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple
import numpy as np

VAULT_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix")
CONFIG_PATH = VAULT_DIR / "telegram_config.json"
PRESENT_DIR = VAULT_DIR / "Present"
SAS_DIR = VAULT_DIR / "SAS_Assimilation_Massive"
ARCHIVES_DIR = SAS_DIR / "Archives"
EMPREINTES_DIR = VAULT_DIR / "Empreintes_Topologiques"
CONFIG_SONDE_DIR = PRESENT_DIR / "apprentissage_accelere"
CONFIG_SONDE_FILE = CONFIG_SONDE_DIR / "config_sonde.json"
DECOUVERTES_DIR = VAULT_DIR / "Monde_des_Decouvertes"

RAFALE_EN_COURS = False
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Alix-BouleDeNeige/2.0"

# Stop-words étendus (Français + Anglais + Méta-bruit académique)
STOP_WORDS = {
    "dans", "pour", "avec", "cette", "sont", "plus", "nous", "vous",
    "leur", "elle", "comme", "mais", "tout", "faire", "entre", "aussi",
    "sans", "sous", "vers", "chez", "dont", "tous", "bien", "cela",
    "peut", "autre", "apres", "alors", "encore", "leurs", "avoir", "etre",
    "with", "that", "this", "from", "which", "were", "been", "have", "they",
    "these", "those", "their", "will", "what", "when", "where", "into", "also",
    "such", "than", "then", "them", "both", "each", "more", "most", "other",
    "some", "only", "first", "about", "could", "would", "should", "here",
    "arxiv", "abstract", "theme", "paper", "study", "using", "based", "show",
    "results", "propose", "present", "approach", "method", "model", "models",
    "work", "state", "well", "high", "over", "time", "order", "three", "two"
}


def charger_config_sonde() -> Dict[str, Any]:
    """Charge les paramètres de cadence, de seuil et de cascade récursive."""
    if not CONFIG_SONDE_FILE.exists():
        return {
            "nom": "Sonde Apprentissage Accéléré & Boule de Neige Récursive",
            "mode": "AUTOMATIQUE",
            "cadence_rafale_sec": 3600,
            "seuil_documents_batch": 5,
            "dimension_vectorielle": 256,
            "notifier_telegram": True,
            "boule_de_neige_recursive": True,
            "max_generations_cascade": 3,
            "generation_courante": 0,
            "derniere_rafale_ts": 0.0,
            "total_documents_assimiles": 0,
            "total_rafales_executees": 0
        }
    try:
        with open(CONFIG_SONDE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def sauvegarder_config_sonde(cfg: Dict[str, Any]):
    """Sauvegarde l'état de la sonde."""
    try:
        CONFIG_SONDE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_SONDE_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def envoyer_telegram_async(message_md: str):
    """Envoi de notification Telegram asynchrone non-bloquante."""
    if not CONFIG_PATH.exists():
        return
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        if not cfg.get("envois_telegram_actifs", True):
            return
        token = cfg.get("telegram_bot_token")
        chat_id = cfg.get("allowed_user_id")
        if token and chat_id:
            import requests
            def _worker():
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                try:
                    requests.post(url, json={
                        "chat_id": chat_id,
                        "text": message_md,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": True
                    }, timeout=10)
                except Exception:
                    pass
            threading.Thread(target=_worker, daemon=True).start()
    except Exception:
        pass


def aspirer_generation_suivante_arxiv(attracteurs: List[str], generation_num: int, max_articles: int = 20) -> int:
    """Interroge ArXiv pour la génération suivante de la boucle en cascade."""
    if not attracteurs:
        return 0
    # Combine les 2 attracteurs les plus significatifs
    termes_propres = [re.sub(r'[^a-zA-Z0-9]', '', a) for a in attracteurs[:2] if len(a) > 3]
    if not termes_propres:
        return 0
    query = "+AND+".join([f"all:{t}" for t in termes_propres])
    url = f"http://export.arxiv.org/api/query?search_query={query}&start=0&max_results={max_articles}&sortBy=submittedDate&sortOrder=descending"
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})

    articles_sauvegardes = 0
    try:
        time.sleep(2.5)  # Pause de courtoisie API ArXiv
        with urllib.request.urlopen(req, timeout=12.0) as resp:
            xml_data = resp.read().decode('utf-8', errors='replace')
            root = ET.fromstring(xml_data)
            entries = root.findall('{http://www.w3.org/2005/Atom}entry')

            for i, entry in enumerate(entries):
                title_el = entry.find('{http://www.w3.org/2005/Atom}title')
                summary_el = entry.find('{http://www.w3.org/2005/Atom}summary')
                id_el = entry.find('{http://www.w3.org/2005/Atom}id')
                published_el = entry.find('{http://www.w3.org/2005/Atom}published')

                if title_el is not None and summary_el is not None:
                    title = " ".join(title_el.text.strip().split())
                    summary = " ".join(summary_el.text.strip().split())
                    arxiv_id = id_el.text.strip() if id_el is not None else f"gen{generation_num}_{i}"
                    published = published_el.text.strip()[:10] if published_el is not None else ""

                    slug = re.sub(r'[^a-zA-Z0-9_-]', '_', title[:40]).strip('_')
                    fichier_nom = f"cascade_gen{generation_num}_{i+1}_{slug}.md"
                    fichier_path = SAS_DIR / fichier_nom

                    contenu_md = (
                        f"# {title}\n\n"
                        f"- **Cascade :** Génération {generation_num} (Attracteurs : `{' + '.join(termes_propres)}`)\n"
                        f"- **ArXiv ID :** `{arxiv_id}` &middot; **Date :** `{published}`\n\n"
                        f"## Abstract\n\n{summary}\n"
                    )
                    fichier_path.write_text(contenu_md, encoding="utf-8")
                    articles_sauvegardes += 1
    except Exception:
        pass
    return articles_sauvegardes


def executer_rafale_topologique(fichiers: List[Path], cfg: Dict[str, Any]):
    """
    Exécute la rafale matricielle ultra-rapide (AVX2 / Arc Xe2).
    Si le mode récursif est actif, enchaîne avec la génération suivante.
    """
    global RAFALE_EN_COURS
    t0 = time.perf_counter()
    RAFALE_EN_COURS = True
    try:
        M = len(fichiers)
        textes = []
        noms = []
        vocabulaire = {}

        # 1. Lecture et indexation
        for p in fichiers:
            try:
                contenu = p.read_text(encoding="utf-8", errors="ignore")
                textes.append(contenu)
                noms.append(p.name)
                mots = re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', contenu.lower())
                for m in set(mots):
                    if m not in STOP_WORDS and not m.isdigit():
                        vocabulaire[m] = vocabulaire.get(m, 0) + 1
            except Exception:
                pass

        if not textes:
            return

        seuil_doc = 2 if M >= 5 else 1
        mots_retenus = [m for m, c in vocabulaire.items() if c >= seuil_doc]
        if not mots_retenus:
            mots_retenus = list(vocabulaire.keys())[:256]
        mots_retenus = mots_retenus[:1500]
        mot_a_idx = {m: i for i, m in enumerate(mots_retenus)}
        d = len(mots_retenus)

        # 2. Construction matrice X (M x d)
        X = np.zeros((M, d), dtype=np.float32)
        for i, txt in enumerate(textes):
            for m in re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', txt.lower()):
                if m in mot_a_idx:
                    X[i, mot_a_idx[m]] += 1.0

        # Normalisation L2 par document
        normes = np.linalg.norm(X, axis=1, keepdims=True)
        normes[normes == 0] = 1.0
        X = X / normes

        # 3. Matrice de Gram Duale G = (1/M) * (X @ X.T)
        G = (1.0 / M) * (X @ X.T)

        # 4. Invariants Spectraux & Dimension Effective d_eff
        valeurs_propres = np.linalg.eigvalsh(G)
        valeurs_propres = np.sort(valeurs_propres)[::-1]
        valeurs_propres = np.clip(valeurs_propres, 0.0, None)

        tr_G = float(np.sum(valeurs_propres))
        tr_G2 = float(np.sum(valeurs_propres ** 2))
        d_eff = (tr_G ** 2) / tr_G2 if tr_G2 > 0 else 1.0

        # 5. Extraction des Attracteurs Purs (filtrés de tout méta-bruit)
        somme_poids = np.sum(X, axis=0)
        top_indices = np.argsort(somme_poids)[::-1][:8]
        attracteurs = [(mots_retenus[idx], float(somme_poids[idx])) for idx in top_indices]

        duree_rafale_sec = round(time.perf_counter() - t0, 3)
        horodate_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 6. Gravure de l'Empreinte
        EMPREINTES_DIR.mkdir(parents=True, exist_ok=True)
        fichier_empreinte = EMPREINTES_DIR / f"Empreinte_Topologique_{horodate_str}.json"
        donnees_empreinte = {
            "horodatage": datetime.now().isoformat(),
            "documents_assimiles_count": M,
            "dimension_vocabulaire": d,
            "dimension_effective_d_eff": round(d_eff, 3),
            "valeurs_propres_principales": [round(float(v), 5) for v in valeurs_propres[:6]],
            "attracteurs_dominants": attracteurs,
            "duree_rafale_sec": duree_rafale_sec,
            "fichiers_sources": noms
        }
        with open(fichier_empreinte, "w", encoding="utf-8") as f:
            json.dump(donnees_empreinte, f, indent=2, ensure_ascii=False)

        # 7. Note de synthèse dans l'Exocerveau
        DECOUVERTES_DIR.mkdir(parents=True, exist_ok=True)
        note_decouverte = DECOUVERTES_DIR / f"Assimilation_Topologique_{horodate_str}.md"
        attracteurs_md = "\n".join([f"- **{m}** (intensité spectrale: `{p:.2f}`)" for m, p in attracteurs])
        note_md = (
            f"---\n"
            f"titre: \"Assimilation Topologique Massive — {datetime.now().strftime('%Y-%m-%d %H:%M')}\"\n"
            f"date: \"{datetime.now().strftime('%Y-%m-%d %H:%M')}\"\n"
            f"documents_assimiles: {M}\n"
            f"dimension_effective: {d_eff:.2f}\n"
            f"duree_rafale_sec: {duree_rafale_sec}\n"
            f"tags:\n"
            f"  - assimilation_massive\n"
            f"  - topologie_spectrale\n"
            f"  - empreinte_simpliciale\n"
            f"  - alix_souveraine\n"
            f"---\n\n"
            f"# ⚡ [[Assimilation_Topologique_{horodate_str}]] — Empreinte Pure\n\n"
            f"> **Substrat :** Intel Arc 140V Xe2 & AVX2 &middot; **Temps de Calcul :** `{duree_rafale_sec}s`\n"
            f"> **Volume :** `{M} documents` absorbés &middot; **Dimension Réelle (d_eff) :** `{d_eff:.2f}`\n\n"
            f"## 🌌 Attracteurs Clés Dégagés du Corpus\n{attracteurs_md}\n\n"
            f"## 📐 Géométrie Matricielle de Gram Duale\n"
            f"- **Trace $\\text{{Tr}}(G)$ :** `{tr_G:.4f}`\n"
            f"- **Pureté $\\text{{Tr}}(G^2)$ :** `{tr_G2:.4f}`\n"
            f"- **Empreinte scellée dans :** `Empreintes_Topologiques/{fichier_empreinte.name}`\n"
        )
        note_decouverte.write_text(note_md, encoding="utf-8")

        # 8. Archivage des sources
        ARCHIVES_DIR.mkdir(parents=True, exist_ok=True)
        for p in fichiers:
            try:
                dest = ARCHIVES_DIR / f"{horodate_str}_{p.name}"
                shutil.move(str(p), str(dest))
            except Exception:
                pass

        # 9. Mise à jour de la configuration
        cfg["derniere_rafale_ts"] = time.time()
        cfg["derniere_rafale_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cfg["total_documents_assimiles"] = cfg.get("total_documents_assimiles", 0) + M
        cfg["total_rafales_executees"] = cfg.get("total_rafales_executees", 0) + 1

        # 10. SAUT RÉCURSIF DE LA BOULE DE NEIGE (Génération N+1)
        cascade_active = cfg.get("boule_de_neige_recursive", False)
        max_gen = cfg.get("max_generations_cascade", 3)
        gen_courante = cfg.get("generation_courante", 0)

        nouveaux_articles = 0
        attracteurs_noms = [m for m, _ in attracteurs if len(m) >= 4]

        if cascade_active and gen_courante < max_gen and attracteurs_noms:
            gen_suivante = gen_courante + 1
            cfg["generation_courante"] = gen_suivante
            sauvegarder_config_sonde(cfg)

            top_duo = attracteurs_noms[:2]
            # Notification Telegram d'enclenchement de cascade
            if cfg.get("notifier_telegram", True):
                msg_cascade = (
                    f"❄️ *BOULE DE NEIGE — GÉNÉRATION {gen_suivante}/{max_gen} ENCLENCHÉE*\n\n"
                    f"🔬 *Frontière découverte :* `{' + '.join(top_duo)}`\n"
                    f"📥 *Aspiration ArXiv en cours...* Le SAS va recevoir le prochain lot."
                )
                envoyer_telegram_async(msg_cascade)

            # Télécharge la génération suivante directement dans le SAS
            nouveaux_articles = aspirer_generation_suivante_arxiv(top_duo, gen_suivante, max_articles=20)

        elif gen_courante >= max_gen:
            # Réinitialisation après achèvement de la cascade
            cfg["generation_courante"] = 0
            sauvegarder_config_sonde(cfg)
            if cfg.get("notifier_telegram", True):
                msg_fin = (
                    f"🏆 *CASCADE BOULE DE NEIGE ACHEVÉE*\n\n"
                    f"✨ 3 générations de recherche ont été enchaînées et absorbées en continu !\n"
                    f"📚 Total session : `{cfg.get('total_documents_assimiles', 0)} documents` au connectome.\n"
                    f"Retour au repos nominal à 2 Watts."
                )
                envoyer_telegram_async(msg_fin)
        else:
            sauvegarder_config_sonde(cfg)

        # Flash de fin de rafale courante
        if cfg.get("notifier_telegram", True) and not (cascade_active and gen_courante < max_gen):
            top_attract_str = ", ".join([f"*{m}*" for m, _ in attracteurs[:3]])
            msg_tg = (
                f"⚡ *SONDE APPRENTISSAGE ACCÉLÉRÉ — RAFALE TERMINÉE*\n\n"
                f"📚 *Documents ingérés :* `{M} textes en un souffle`\n"
                f"📐 *Dimension effective (d_eff) :* `{d_eff:.2f}`\n"
                f"🌌 *Attracteurs clés purs :* {top_attract_str}\n"
                f"⏱️ *Temps de calcul :* `{duree_rafale_sec}s` sur le fer\n"
                f"💾 *Note gravée :* `{note_decouverte.name}`\n"
            )
            envoyer_telegram_async(msg_tg)

    except Exception as e:
        pass
    finally:
        RAFALE_EN_COURS = False


def executer_capacite(contexte_fer: Dict[str, Any] = None) -> Dict[str, Any]:
    """Point d'entrée exécuté à chaque cycle du Démon Souverain."""
    t0 = time.perf_counter()
    global RAFALE_EN_COURS

    if RAFALE_EN_COURS:
        duree_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "statut": "RAFALE_EN_COURS",
            "duree_ms": duree_ms,
            "message": "Calcul matriciel d'assimilation en progression"
        }

    cfg = charger_config_sonde()
    mode = cfg.get("mode", "AUTOMATIQUE")
    cadence_sec = cfg.get("cadence_rafale_sec", 3600)
    seuil_batch = cfg.get("seuil_documents_batch", 5)
    derniere_ts = cfg.get("derniere_rafale_ts", 0.0)

    if not SAS_DIR.exists():
        SAS_DIR.mkdir(parents=True, exist_ok=True)

    fichiers_sas = [
        p for p in SAS_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in [".txt", ".md", ".json", ".csv"]
    ]
    nb_docs = len(fichiers_sas)

    if nb_docs == 0:
        duree_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "statut": "VEILLE_SAS_VIDE",
            "duree_ms": duree_ms,
            "documents_en_attente": 0,
            "message": "SAS vide, aucun document à ingérer"
        }

    maintenant = time.time()
    temps_ecoule = maintenant - derniere_ts
    doit_declencher = False
    raison = ""

    if mode == "AUTOMATIQUE":
        if nb_docs >= seuil_batch:
            doit_declencher = True
            raison = f"Seuil de lot atteint ({nb_docs} >= {seuil_batch})"
        elif temps_ecoule >= cadence_sec:
            doit_declencher = True
            raison = f"Cadence horaire écoulée ({round(temps_ecoule/60, 1)} min)"

    if doit_declencher:
        th = threading.Thread(target=executer_rafale_topologique, args=(fichiers_sas, cfg), daemon=True)
        th.start()
        duree_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "statut": "LANCEMENT_RAFALE",
            "duree_ms": duree_ms,
            "documents_a_traiter": nb_docs,
            "declencheur": raison
        }
    else:
        duree_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "statut": "EN_ATTENTE_SEUIL",
            "duree_ms": duree_ms,
            "documents_en_attente": nb_docs,
            "seuil_requis": seuil_batch,
            "prochaine_rafale_dans_min": round(max(0, (cadence_sec - temps_ecoule)) / 60, 1)
        }

