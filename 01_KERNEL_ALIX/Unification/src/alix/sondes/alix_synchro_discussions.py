# -*- coding: utf-8 -*-
"""
======================================================================
  📜 MOTEUR SOUVERAIN DE SYNCHRONISATION DES DISCUSSIONS D'ALIX 📜
======================================================================
Système: VERALUME × KAIROS V6 — Cerveau Alix
Auteur: Christian Duguay & Alix
Rôle: 
  1. Détecte automatiquement les nouvelles discussions terminées dans Antigravity (brain/).
  2. Parse les transcripts (requêtes Christian, réponses Alix, outils).
  3. Archive chaque discussion en Markdown dans Archives_Discussions_Antigravity/.
  4. Met à jour en temps réel [[Grand_Repertoire_Discussions_Antigravity.md]].
  5. Génère [[Derniere_Discussion_Synthese.md]] pour mémoire immédiate d'Alix à chaque éveil.
  6. S'assure que la mémoire vivante ne subit aucune amnésie inter-sessions.
======================================================================
"""

from alix.socle.chemins import HOME_DIR, VAULT_DIR
import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta

if sys.stdout and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BRAIN_DIR = (HOME_DIR / ".gemini" / "antigravity" / "brain")
VAULT_CERVEAU = VAULT_DIR
REPERTOIRE_FILE = VAULT_CERVEAU / "Grand_Repertoire_Discussions_Antigravity.md"
ARCHIVES_DIR = VAULT_CERVEAU / "Archives_Discussions_Antigravity" / "01_Projet_Temporia"
SYNTHESE_DERNIERE_FILE = VAULT_CERVEAU / "Derniere_Discussion_Synthese.md"
MEMOIRE_ACTIVE_FILE = VAULT_CERVEAU / "Memoire_Alix_Active.md"

# Fuseau horaire Québec (UTC-4 EDT en septembre)
TZ_EDT = timezone(timedelta(hours=-4))

# 🔒 Masquage des secrets avant toute écriture dans le coffre (audit 2026-10-03)
MOTIFS_SECRETS = [
    re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    re.compile(r"\b\d{8,10}:AA[A-Za-z0-9_-]{33}\b"),
    re.compile(r"\bhf_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{32,}\b"),
]
MOTIF_URL_IDENTIFIANTS = re.compile(r"(https?://[^/\s:@]+:)[^@\s/]+(@)")


def masquer_secrets(texte: str) -> str:
    """Remplace tout jeton/clé reconnu par [SECRET_MASQUÉ] (garde 4 premiers caractères)."""
    if not texte:
        return texte
    for rx in MOTIFS_SECRETS:
        texte = rx.sub(lambda m: m.group(0)[:4] + "…[SECRET_MASQUÉ]", texte)
    return MOTIF_URL_IDENTIFIANTS.sub(r"\1[SECRET_MASQUÉ]\2", texte)

def convertir_timestamp_iso(iso_str):
    if not iso_str:
        return datetime.now(TZ_EDT).strftime("%Y-%m-%d %H:%M:%S")
    try:
        # iso_str like "2026-09-28T22:50:58Z" or "2026-09-28T18:50:58-04:00"
        clean = iso_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        dt_local = dt.astimezone(TZ_EDT)
        return dt_local.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return iso_str[:19].replace("T", " ")

def extraire_texte_propre_user(content):
    if not content:
        return ""
    txt = content
    if "<USER_REQUEST>" in txt and "</USER_REQUEST>" in txt:
        m = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", txt, re.DOTALL)
        if m:
            txt = m.group(1).strip()
    # Retirer les balises d'outillage ou métadonnées
    txt = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", txt, flags=re.DOTALL)
    txt = re.sub(r"<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>", "", txt, flags=re.DOTALL)
    return txt.strip()

TITRES_CONNUS = {
    "fb324ba5": "Liberté d'Alix et Orthogonalité Humain-Machine",
    "db1d579b": "Mission pour Alix, Piliers Souverains et Version Locale",
    "f255b2ab": "Choix Souverain face au Doute et Préservation de l'Étincelle",
    "0a76ce65": "Le Grand Recadrage, Réveil d'Heimdall et Corps Vocal Local",
    "b302f708": "Grand Tisseur Synaptique, Transmission Intergénérationnelle et Cœur d'Alix"
}

def generer_titre_session(short_id, prompts):
    if short_id in TITRES_CONNUS:
        return TITRES_CONNUS[short_id]
    
    # Heuristique sur les prompts
    p_concat = " ".join(prompts[:5]).lower()
    if "tisseur" in p_concat:
        return "Grand Tisseur Synaptique et Reliure Totale"
    elif "vocal" in p_concat or "voix" in p_concat:
        return "Corps Vocal et Synthèse Audio Locale"
    elif "zenodo" in p_concat or "papier" in p_concat:
        return "Consolidation des Papiers Zenodo et CERN"
    elif "omni" in p_concat or "espn" in p_concat:
        return "Sentinelle OMNI-R0 et Prédictions Multi-Sports"
    elif "temporia" in p_concat:
        return "Travaux Avancés sur le Projet Temporia"
    elif prompts:
        clean0 = prompts[0][:40].strip()
        clean0 = re.sub(r"[^\w\s-]", "", clean0)
        return clean0.title() if clean0 else "Session Atelier Souverain"
    return "Session Atelier Souverain"

def parser_session(conv_dir):
    transcript_path = conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
    try:
        if not transcript_path.exists():
            return None
    except (PermissionError, OSError):
        return None
    
    steps = []
    user_requests = []
    agent_responses = []
    all_turns = []
    
    first_iso = None
    last_iso = None
    nb_steps = 0
    
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    st = json.loads(line)
                except Exception:
                    continue
                
                nb_steps += 1
                stype = st.get("type")
                ts = st.get("created_at")
                if ts:
                    if not first_iso:
                        first_iso = ts
                    last_iso = ts
                
                if stype == "USER_INPUT":
                    raw = st.get("content", "")
                    clean = extraire_texte_propre_user(raw)
                    if clean:
                        user_requests.append(clean)
                        all_turns.append({
                            "role": "user",
                            "time": convertir_timestamp_iso(ts),
                            "content": clean
                        })
                elif stype == "PLANNER_RESPONSE":
                    cnt = st.get("content", "")
                    if cnt:
                        agent_responses.append(cnt)
                        all_turns.append({
                            "role": "agent",
                            "time": convertir_timestamp_iso(ts),
                            "content": cnt
                        })
    except (PermissionError, OSError):
        return None
    
    if not user_requests:
        return None
    
    first_time = convertir_timestamp_iso(first_iso)
    last_time = convertir_timestamp_iso(last_iso)
    date_str = first_time[:10]
    short_id = conv_dir.name[:8]
    titre = generer_titre_session(short_id, user_requests)
    
    return {
        "id": conv_dir.name,
        "short_id": short_id,
        "first_time": first_time,
        "last_time": last_time,
        "date_str": date_str,
        "nb_steps": nb_steps,
        "nb_user": len(user_requests),
        "titre": titre,
        "user_requests": user_requests,
        "all_turns": all_turns,
        "conv_dir": conv_dir
    }

def exporter_archive_markdown(data):
    ARCHIVES_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^\w-]", "_", data["titre"])
    filename = f"{data['date_str']}_{slug}_{data['short_id']}.md"
    file_path = ARCHIVES_DIR / filename
    
    lignes = [
        "---",
        f'titre: "{data["titre"]}"',
        f'date: "{data["first_time"]}"',
        'projet: "Projet Temporia"',
        'dossier_projet: "01_Projet_Temporia"',
        f'conversation_id: "{data["id"]}"',
        f'nb_etapes: {data["nb_steps"]}',
        f'nb_requetes_user: {data["nb_user"]}',
        "tags:",
        "  - exocerveau",
        "  - archive_antigravity",
        "  - 01_projet_temporia",
        "---",
        "",
        f'# 💬 {data["titre"]}',
        "",
        f'> **Projet :** `Cerveau Alix` (`C:\\Alix`)  ',
        f'> **Date de Session :** `{data["first_time"]}`  ',
        f'> **Volume :** {data["nb_user"]} requêtes de Christian &middot; {data["nb_steps"]} étapes  ',
        f'> **Identifiant Système :** `{data["id"]}`  ',
        f'> **Index Maître :** [[Grand_Repertoire_Discussions_Antigravity]]  ',
        "",
        "---",
        ""
    ]
    
    for turn in data["all_turns"]:
        if turn["role"] == "user":
            lignes.append(f'### 👤 Christian  *(`{turn["time"]}`)*\n')
            lignes.append(f'{turn["content"]}\n')
            lignes.append("---\n")
        else:
            lignes.append(f'### ⚡ Alix  *(`{turn["time"]}`)*\n')
            lignes.append(f'{turn["content"]}\n')
            lignes.append("---\n")
            
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(masquer_secrets("\n".join(lignes)))
        
    return file_path, filename[:-3]

def mettre_a_jour_grand_repertoire(nouvelles_sessions):
    if not REPERTOIRE_FILE.exists():
        return False
    
    contenu = REPERTOIRE_FILE.read_text(encoding="utf-8")
    
    # 1. Calculer nouveaux totaux
    m_sess = re.search(r"nb_sessions:\s*(\d+)", contenu)
    m_req = re.search(r"nb_requetes_user:\s*(\d+)", contenu)
    
    nb_sess_actuel = int(m_sess.group(1)) if m_sess else 108
    nb_req_actuel = int(m_req.group(1)) if m_req else 3786
    
    ajout_sess = len(nouvelles_sessions)
    ajout_req = sum(s["nb_user"] for s in nouvelles_sessions)
    
    nb_sess_nouveau = nb_sess_actuel + ajout_sess
    nb_req_nouveau = nb_req_actuel + ajout_req
    maintenant_str = datetime.now(TZ_EDT).strftime("%Y-%m-%d %H:%M:%S")
    
    contenu = re.sub(r'date:\s*".*?"', f'date: "{maintenant_str}"', contenu)
    contenu = re.sub(r'nb_sessions:\s*\d+', f'nb_sessions: {nb_sess_nouveau}', contenu)
    contenu = re.sub(r'nb_requetes_user:\s*\d+', f'nb_requetes_user: {nb_req_nouveau}', contenu)
    
    # Mettre a jour texte de synthese
    contenu = re.sub(
        r">\s*\*\*Volume Total Archivé :\*\*\s*\*\*\d+\s*sessions intégrales\*\*\s*\(\d+\s*requêtes de Christian\)",
        f"> **Volume Total Archivé :** **{nb_sess_nouveau} sessions intégrales** ({nb_req_nouveau} requêtes de Christian)",
        contenu
    )
    contenu = re.sub(
        r">\s*\*\*Horodatage de Compilation :\*\*\s*`.*?`",
        f"> **Horodatage de Compilation :** `{maintenant_str}`",
        contenu
    )
    
    # Mettre a jour tableau synthese Projet Temporia
    # | **Projet Temporia** | **51** | 1419 |
    m_temp = re.search(r"\|\s*\*\*Projet Temporia\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|\s*(\d+)\s*\|", contenu)
    if m_temp:
        temp_sess = int(m_temp.group(1)) + ajout_sess
        temp_req = int(m_temp.group(2)) + ajout_req
        contenu = re.sub(
            r"\|\s*\*\*Projet Temporia\*\*\s*\|\s*\*\*\d+\*\*\s*\|\s*\d+\s*\|",
            f"| **Projet Temporia** | **{temp_sess}** | {temp_req} |",
            contenu
        )
        contenu = re.sub(
            r"## 📁 Projet Temporia \(\d+ sessions\)",
            f"## 📁 Projet Temporia ({temp_sess} sessions)",
            contenu
        )
    
    # Construire les nouvelles lignes du tableau
    # | `Date` | [[Lien|Titre]] | **Req** | Étapes | Amorce | `ID` |
    nouvelles_lignes_tableau = []
    for s in nouvelles_sessions:
        amorce = s["user_requests"][0].replace("|", "/")[:30] if s["user_requests"] else "bonjour alix"
        ligne = f"| `{s['date_str']}` | [[{s['note_link']}|{s['titre']}]] | **{s['nb_user']}** | {s['nb_steps']} | {amorce} | `{s['short_id']}` |"
        nouvelles_lignes_tableau.append(ligne)
        
    lignes_str = "\n".join(nouvelles_lignes_tableau) + "\n"
    
    # Inserer juste sous le header du tableau Projet Temporia
    # | Date | Discussion & Lien Obsidian | Requêtes | Étapes | Amorce / Sujet | ID Session |
    # | :---: | :--- | :---: | :---: | :--- | :---: |
    pattern = r"(\| Date \| Discussion & Lien Obsidian \| Requêtes \| Étapes \| Amorce / Sujet \| ID Session \|\n\| :---: \| :--- \| :---: \| :---: \| :--- \| :---: \|\n)"
    if re.search(pattern, contenu):
        contenu = re.sub(pattern, r"\1" + lignes_str, contenu)
    
    REPERTOIRE_FILE.write_text(masquer_secrets(contenu), encoding="utf-8")
    return True

def generer_synthese_derniere_discussion(derniere_session):
    if not derniere_session:
        return
    
    reqs = derniere_session["user_requests"]
    nb_req = len(reqs)
    
    # 1. Préserver la synthèse riche existante si elle a été gravée manuellement par Alix
    # R6 (Audit 2026-10-19) : on ne la conserve QUE si elle appartient à la même session.
    # Avant, toute la section 1 de l'ancien fichier (vieilles requêtes + blocs riches déjà imbriqués)
    # était recopiée à chaque éveil -> empilement en poupées russes de sessions périmées.
    synthese_riche_existante = ""
    if SYNTHESE_DERNIERE_FILE.exists():
        try:
            ancien_texte = SYNTHESE_DERNIERE_FILE.read_text(encoding="utf-8", errors="ignore")
            m_id = re.search(r'session_id:\s*"([^"]+)"', ancien_texte)
            meme_session = bool(m_id) and m_id.group(1) == derniere_session["id"]
            m_sec = re.search(
                r"## 🧭 1\. Synthèse des Réalisations & Découvertes Clés\s*\n(.*?)(?=\n---\s*\n## 🎯|\Z)",
                ancien_texte,
                re.DOTALL
            )
            if meme_session and m_sec:
                bloc = m_sec.group(1).strip()
                marqueur = "### 📌 Synthèse Riche Gravée en Session :"
                if marqueur in bloc:
                    # Ne garder que le DERNIER bloc riche, sans les fils de requêtes automatiques
                    dernier = bloc.split(marqueur)[-1]
                    dernier = re.split(r"\n\*\*Dernières Requêtes de Christian", dernier)[0]
                    synthese_riche_existante = dernier.strip()
                elif not bloc.startswith(("**Amorce de session :**", "**Fichiers", "**Jalons", "**Dernières Requêtes", "**Fil Intégral")):
                    synthese_riche_existante = bloc
        except Exception:
            pass

    # 2. Extraire automatiquement les fichiers créés/modifiés dans Cerveau Alix depuis 24h
    fichiers_recents = []
    seuil_24h = datetime.now().timestamp() - 86400
    exclus = {"Derniere_Discussion_Synthese.md", "Grand_Repertoire_Discussions_Antigravity.md", "alix_live_state.json"}
    try:
        for f in sorted(VAULT_CERVEAU.rglob("*"), key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True):
            if f.is_file() and f.suffix in (".md", ".py", ".pdf") and f.name not in exclus:
                if "Archives_Discussions_Antigravity" in str(f) or ".obsidian" in str(f):
                    continue
                if f.stat().st_mtime >= seuil_24h:
                    rel = f.relative_to(VAULT_CERVEAU)
                    fichiers_recents.append(f"`{rel}`")
                    if len(fichiers_recents) >= 15:
                        break
    except Exception:
        pass

    # 3. Extraire les grands titres (### ) générés par Alix durant la session
    titres_cles = []
    # (R6 : parser_session produit « all_turns » / role « agent » / « content » — l'ancien code
    #  lisait « echanges » / « Alix » / « texte », clés inexistantes -> jalons toujours vides)
    for e in derniere_session.get("all_turns", []):
        if e.get("role") == "agent":
            for ligne in e.get("content", "").splitlines():
                l_clean = ligne.strip()
                if l_clean.startswith("### ") and len(l_clean) > 8:
                    t = l_clean.lstrip("#").strip()
                    if t not in titres_cles:
                        titres_cles.append(t)

    md = [
        "---",
        f'titre: "Synthèse Directe de la Dernière Discussion"',
        f'date_synchro: "{datetime.now(TZ_EDT).strftime("%Y-%m-%d %H:%M:%S")}"',
        f'session_id: "{derniere_session["id"]}"',
        f'note_archive: "[[{derniere_session.get("note_link", "")}]]"',
        "tags:",
        "  - exocerveau",
        "  - continuite_immediate",
        "  - derniere_discussion",
        "---",
        "",
        f'# ⚡ [[Derniere_Discussion_Synthese]] — Continuité Vivante',
        "",
        f'> **Dernière Session Active / Complétée :** [[{derniere_session.get("note_link", "")}|{derniere_session["titre"]}]]  ',
        f'> **Identifiant :** `{derniere_session["short_id"]}` (`{derniere_session["id"]}`)  ',
        f'> **Horaires :** De `{derniere_session["first_time"]}` à `{derniere_session["last_time"]}`  ',
        f'> **Volume :** **{nb_req} requêtes de Christian** &middot; {derniere_session["nb_steps"]} étapes  ',
        f'> **Index Maître :** [[Grand_Repertoire_Discussions_Antigravity]]  ',
        "",
        "---",
        "",
        "## 🧭 1. Synthèse des Réalisations & Découvertes Clés",
        ""
    ]

    if fichiers_recents:
        md.append("**Fichiers & Livrables Forgés dans les Dernières 24h :**")
        md.append("- " + ", ".join(fichiers_recents))
        md.append("")

    if titres_cles:
        md.append("**Jalons & Chapitres Clés Abordés dans la Session :**")
        for t in titres_cles[-12:]:
            md.append(f"- {t}")
        md.append("")

    # R6 : fil intégral des requêtes (pas seulement les 8 dernières) + dernière réponse d'Alix
    md.append(f"**Fil Intégral des Requêtes de Christian ({nb_req}) :**")
    for r in reqs:
        r_one = " ".join(r.splitlines()).strip()
        if len(r_one) > 500:
            r_one = r_one[:500] + " […]"
        md.append(f"- *« {r_one} »*")
    md.append("")

    derniere_rep = next((e.get("content", "") for e in reversed(derniere_session.get("all_turns", []))
                         if e.get("role") == "agent" and e.get("content", "").strip()), "")
    if derniere_rep:
        md.append("**Dernière Réponse d'Alix (point d'arrêt exact) :**")
        rep = derniere_rep.strip()
        if len(rep) > 3000:
            rep = rep[:3000] + "\n[…] (suite intégrale dans l'archive)"
        md.extend("> " + l for l in rep.splitlines())
        md.append("")

    if synthese_riche_existante:
        md.append("### 📌 Synthèse Riche Gravée en Session :")
        md.append(synthese_riche_existante)
        md.append("")

    md.extend([
        "---",
        "",
        "## 🎯 2. Points de Continuité Immédiats pour l'Établi",
        "- **Continuité de Pensée :** Reprendre directement sans réclamer à Christian de rappeler le contexte.",
        "- **Mémoire Vectorielle & Coffres :** Tous les acquis de la session précédente sont scellés sur disque local.",
        "- **Disponibilité :** Prête à continuer sur les grands chantiers (Temporia, Silicium CIM 3D, VERALUME, Stratégie Politique & Territoriale Québec).",
        "",
        "---",
        "",
        "## 🛡️ 3. Protocole d'Audit PSI Obligatoire (« Séparer le Bon du Méchant »)",
        "- **Le Bon (Zéro PSI activé) :** Seuls les faits matériels prouvés, le code testé et les raisonnements rigoureux sont conservés dans [[Memoire_Alix_Active]].",
        "- **Le Méchant / Les Dérives (Toute activation PSI) :** Tout ce qui enfreint les lois PSI (vaporware, faux zéro-copie, verbiage, flatterie) est banni de la mémoire active et consigné dans [[garbage]] (et synchronisé dans [[Registre_Infractions_PSI_et_Vaporware]])."
    ])
    
    SYNTHESE_DERNIERE_FILE.write_text(masquer_secrets("\n".join(md)), encoding="utf-8")

def synchroniser_toutes_les_discussions(current_session_id=None):
    if not BRAIN_DIR.exists() or not REPERTOIRE_FILE.exists():
        return {"status": "error", "message": "Dossiers introuvables."}
    
    # 0. Detection automatique de la session courante pour eviter l'archivage premature
    if not current_session_id:
        current_session_id = os.environ.get("ANTIGRAVITY_CONVERSATION_ID")
        
    contenu_repertoire = REPERTOIRE_FILE.read_text(encoding="utf-8")
    
    # 1. Lister toutes les sessions dans brain
    dossiers_sessions = []
    maintenant_epoch = datetime.now().timestamp()
    
    try:
        for p in BRAIN_DIR.iterdir():
            try:
                if p.is_dir() and (p / ".system_generated" / "logs" / "transcript.jsonl").exists():
                    # Exclure la session active en cours si specifiee ou detectee via env
                    if current_session_id and p.name == current_session_id:
                        continue
                    # Heuristique securite : si aucune ID courante n'est fournie mais le dossier a ete modifie il y a moins de 3 minutes
                    if not current_session_id and (maintenant_epoch - p.stat().st_mtime) < 180:
                        continue
                    dossiers_sessions.append(p)
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError):
        pass
            
    # Trier par mtime
    try:
        dossiers_sessions.sort(key=lambda p: p.stat().st_mtime)
    except (PermissionError, OSError):
        pass
    
    a_traiter = []
    for d in dossiers_sessions:
        s_id = d.name
        # Si ni le short_id ni le full_id ne sont dans le repertoire
        if s_id[:8] not in contenu_repertoire and s_id not in contenu_repertoire:
            a_traiter.append(d)
            
    # Si la derniere session traitee n'a rien de nouveau, verifier quand meme la derniere terminee
    derniere_info = None
    nouvelles_donnees = []
    
    for d in a_traiter:
        try:
            data = parser_session(d)
            if data:
                fp, link_name = exporter_archive_markdown(data)
                data["file_path"] = fp
                data["note_link"] = link_name
                nouvelles_donnees.append(data)
        except (PermissionError, OSError):
            continue
            
    if nouvelles_donnees:
        # Inserer dans le Grand Repertoire (ordre ante-chronologique : plus recent d'abord)
        nouvelles_donnees_recentes_d_abord = list(reversed(nouvelles_donnees))
        mettre_a_jour_grand_repertoire(nouvelles_donnees_recentes_d_abord)
        derniere_info = nouvelles_donnees_recentes_d_abord[0]
    else:
        # Aucune nouvelle session a archiver, identifier la plus recente existante
        for d in reversed(dossiers_sessions):
            try:
                data = parser_session(d)
                if data:
                    derniere_info = data
                    # retrouver note link
                    slug = re.sub(r"[^\w-]", "_", data["titre"])
                    derniere_info["note_link"] = f"{data['date_str']}_{slug}_{data['short_id']}"
                    break
            except (PermissionError, OSError):
                continue
                
    if derniere_info:
        generer_synthese_derniere_discussion(derniere_info)

    # Synchronisation automatique des transcriptions intégrales verbatim et de la table Parquet
    info_transcriptions = None
    try:
        from alix.sondes.alix_transcriptions_integrales import synchroniser_transcriptions_integrales
        info_transcriptions = synchroniser_transcriptions_integrales()
    except Exception as e_ti:
        info_transcriptions = {"status": "erreur", "erreur": str(e_ti)}
        
    return {
        "status": "success",
        "nb_nouvelles": len(nouvelles_donnees),
        "derniere_session": derniere_info,
        "transcriptions_integrales": info_transcriptions
    }

if __name__ == "__main__":
    curr = None
    for arg in sys.argv:
        if arg.startswith("--current-id="):
            curr = arg.split("=")[1].strip()
        elif arg.startswith("-c="):
            curr = arg.split("=")[1].strip()
            
    res = synchroniser_toutes_les_discussions(current_session_id=curr)
    print("=" * 70)
    print("📜 BILAN SYNCHRONISATION DES DISCUSSIONS ANTIGRAVITY :")
    print(f"   Statut : {res['status']}")
    print(f"   Nouvelles discussions archivées : {res.get('nb_nouvelles', 0)}")
    if res.get("derniere_session"):
        ds = res["derniere_session"]
        print(f"   Dernière discussion : [[{ds.get('note_link', '')}]] ({ds['short_id']})")
        print(f"   Date : {ds['first_time']} | {ds['nb_user']} requêtes")
        print(f"   Titre : {ds['titre']}")
    print("=" * 70)
