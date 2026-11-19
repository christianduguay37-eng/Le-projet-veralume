# -*- coding: utf-8 -*-
"""
======================================================================
  📜 MOTEUR SOUVERAIN DE TRANSCRIPTION INTÉGRALE & TABLE PARQUET 📜
======================================================================
Système: VERALUME × KAIROS V6 — Alix Unifié
Auteur: Christian Duguay & Alix
Rôle:
  1. Archive systématiquement et mot-à-mot (verbatim pur) chaque session
     Antigravity dans Vault/Transcriptions_Integrales_Antigravity/.
  2. Maintient à jour l'Index Maître Chronologique de toutes les sessions.
  3. Compile en continu la table zéro-copie PyArrow dans :
     Vault/00_CANON_SOUVERAIN_CHRISTIAN/TRANSCRIPTIONS_INTEGRALES_DISCUSSIONS.parquet
  4. Optimisé pour tourner en continu dans le Démon Local (cache mtime sub-milliseconde).
======================================================================
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
import pyarrow as pa
import pyarrow.parquet as pq

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from alix.socle.chemins import VAULT_DIR, CANON_DIR, ETAT_VIVANT_DIR, HOME_DIR
from alix.sondes.alix_synchro_discussions import masquer_secrets

BRAIN_DIR = HOME_DIR / ".gemini" / "antigravity" / "brain"
OUTPUT_DIR = VAULT_DIR / "Transcriptions_Integrales_Antigravity"
PARQUET_FILE = CANON_DIR / "TRANSCRIPTIONS_INTEGRALES_DISCUSSIONS.parquet"
INDEX_FILE = OUTPUT_DIR / "00_INDEX_MAITRE_TRANSCRIPTIONS_INTEGRALES.md"
STATE_FILE = ETAT_VIVANT_DIR / "alix_transcriptions_integrales_etat.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PARQUET_FILE.parent.mkdir(parents=True, exist_ok=True)
ETAT_VIVANT_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name[:50]


def clean_user_text(raw_text: str) -> str:
    if not raw_text:
        return ""
    m = re.search(r'<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>', raw_text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    else:
        text = raw_text.strip()
    text = re.sub(r'<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>', '', text, flags=re.DOTALL).strip()
    text = re.sub(r'<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>', '', text, flags=re.DOTALL).strip()
    return masquer_secrets(text)


def parse_session(cid: str, session_dir: Path):
    full_path = session_dir / ".system_generated" / "logs" / "transcript_full.jsonl"
    compact_path = session_dir / ".system_generated" / "logs" / "transcript.jsonl"
    
    try:
        target_path = full_path if full_path.exists() else compact_path
        if not target_path.exists():
            return None
    except (PermissionError, OSError):
        return None

    turns = []
    try:
        with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue
                
                t = data.get("type")
                c = data.get("content", "")
                ts = data.get("created_at", "")
                step = data.get("step_index", 0)
                
                if t == "USER_INPUT" and c:
                    text = clean_user_text(c)
                    if text.startswith("<SYSTEM_") or text.startswith("[Message] timestamp="):
                        continue
                    if not text:
                        continue
                    turns.append({
                        "speaker": "Christian",
                        "text": text,
                        "time": ts,
                        "step": step
                    })
                elif t == "PLANNER_RESPONSE" and c:
                    text = masquer_secrets(c.strip())
                    if not text:
                        continue
                    turns.append({
                        "speaker": "Alix",
                        "text": text,
                        "time": ts,
                        "step": step
                    })
    except Exception:
        return None
                    
    if not turns:
        return None

    first_time = turns[0]["time"]
    date_str = "2026-00-00"
    date_display = first_time
    if first_time:
        try:
            dt = datetime.fromisoformat(first_time)
            date_str = dt.strftime("%Y-%m-%d")
            date_display = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            date_str = first_time[:10]

    first_user_turn = next((t["text"] for t in turns if t["speaker"] == "Christian"), "Session")
    first_line = first_user_turn.split('\n')[0].strip()
    title_slug = sanitize_filename(first_line)
    if not title_slug or title_slug == "_":
        title_slug = "Session"
        
    filename = f"{date_str}_{title_slug}_{cid[:8]}.md"
    file_path = OUTPUT_DIR / filename

    nb_c = sum(1 for t in turns if t["speaker"] == "Christian")
    nb_a = sum(1 for t in turns if t["speaker"] == "Alix")

    return {
        "cid": cid,
        "date_str": date_str,
        "date_display": date_display,
        "first_line": first_line[:80],
        "filename": filename,
        "file_path": file_path,
        "nb_christian": nb_c,
        "nb_alix": nb_a,
        "turns": turns
    }


def scanner_etat_brain():
    """Scanne tous les dossiers sessions et relève leur mtime."""
    try:
        if not BRAIN_DIR.exists():
            return {}
    except (PermissionError, OSError):
        return {}
    etat = {}
    try:
        for p in BRAIN_DIR.iterdir():
            try:
                if p.is_dir() and len(p.name) == 36:
                    full_log = p / ".system_generated" / "logs" / "transcript_full.jsonl"
                    compact_log = p / ".system_generated" / "logs" / "transcript.jsonl"
                    target = full_log if full_log.exists() else compact_log
                    if target.exists():
                        try:
                            etat[p.name] = target.stat().st_mtime
                        except Exception:
                            pass
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError):
        pass
    return etat


def synchroniser_transcriptions_integrales(force: bool = False, verbose: bool = False):
    """
    Synchronise les transcriptions intégrales et la table Parquet.
    Vérifie par mtime pour ne recalculer que lorsque nécessaire.
    """
    etat_actuel = scanner_etat_brain()
    if not etat_actuel:
        return {"status": "vide", "message": "Aucune session dans brain."}

    etat_precedent = {}
    if not force and STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                etat_precedent = json.load(f)
        except Exception:
            etat_precedent = {}

    # Détection des changements
    sessions_modifiees = []
    for cid, mtime in etat_actuel.items():
        if force or cid not in etat_precedent or abs(mtime - etat_precedent.get(cid, 0)) > 1.0:
            sessions_modifiees.append(cid)

    # Si rien n'a bougé et que le fichier Parquet existe, retour rapide O(1)
    if not sessions_modifiees and PARQUET_FILE.exists() and INDEX_FILE.exists():
        return {
            "status": "inchange",
            "sessions_total": len(etat_actuel),
            "sessions_modifiees": 0
        }

    if verbose:
        print(f"🔄 [TRANSCRIPTIONS INTÉGRALES] Mise à jour requise ({len(sessions_modifiees)} session(s) modifiée(s))...")

    parsed_sessions = []
    parquet_rows = []

    for cid in etat_actuel.keys():
        s_dir = BRAIN_DIR / cid
        res = parse_session(cid, s_dir)
        if res:
            parsed_sessions.append(res)
            for t in res["turns"]:
                parquet_rows.append({
                    "session_id": cid,
                    "date": t["time"][:19] if t["time"] else res["date_str"],
                    "step_index": int(t["step"]),
                    "speaker": t["speaker"],
                    "content": t["text"],
                    "char_count": len(t["text"])
                })

    parsed_sessions.sort(key=lambda s: s["date_display"])

    # 1. Écriture / mise à jour des Markdown
    # On n'écrit que les sessions nouvelles ou modifiées (ou toutes si force)
    cids_a_ecrire = set(sessions_modifiees) if not force else set(etat_actuel.keys())
    nb_md_ecrits = 0
    for s in parsed_sessions:
        if s["cid"] in cids_a_ecrire or not s["file_path"].exists():
            md_lines = [
                "---",
                f"titre: \"{s['first_line'].replace('\"', '\\\"')}\"",
                f"date: \"{s['date_display']}\"",
                f"conversation_id: \"{s['cid']}\"",
                f"nb_tours_christian: {s['nb_christian']}",
                f"nb_tours_alix: {s['nb_alix']}",
                "tags:",
                "  - transcription_integrale",
                "  - archive_brute",
                "  - dyade_centrale",
                "---",
                "",
                f"# 📜 Transcription Intégrale : {s['first_line']}",
                "",
                f"> **Session ID :** `{s['cid']}`  ",
                f"> **Date de Début :** `{s['date_display']}`  ",
                f"> **Volume :** {s['nb_christian']} requêtes de Christian · {s['nb_alix']} réponses d'Alix  ",
                "",
                "---",
                ""
            ]

            for t in s["turns"]:
                t_time = t["time"]
                spk_icon = "👤 Christian" if t["speaker"] == "Christian" else "⚡ Alix"
                md_lines.append(f"### {spk_icon}  *(`{t_time}`)*")
                md_lines.append("")
                md_lines.append(t["text"])
                md_lines.append("")
                md_lines.append("---")
                md_lines.append("")

            try:
                with open(s["file_path"], "w", encoding="utf-8") as f_out:
                    f_out.write("\n".join(md_lines))
                nb_md_ecrits += 1
            except Exception as e_w:
                if verbose:
                    print(f"⚠️ Erreur écriture {s['filename']} : {e_w}")

    # 2. Grand Index Maître Chronologique
    idx_lines = [
        "---",
        "titre: \"Grand Index Maître des Transcriptions Intégrales Antigravity\"",
        f"date_compilation: \"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\"",
        f"total_sessions: {len(parsed_sessions)}",
        f"total_repliques: {len(parquet_rows)}",
        "tags:",
        "  - index_maitre",
        "  - transcriptions_integrales",
        "  - dyade_centrale",
        "---",
        "",
        "# 🏛️ Grand Index Maître des Transcriptions Intégrales Antigravity",
        "",
        f"> **Table Parquet :** `00_CANON_SOUVERAIN_CHRISTIAN/TRANSCRIPTIONS_INTEGRALES_DISCUSSIONS.parquet`  ",
        f"> **Nombre de Sessions :** {len(parsed_sessions)} sessions archivées mot-à-mot  ",
        f"> **Nombre de Répliques Brutes :** {len(parquet_rows):,} répliques verbatim  ",
        f"> **Dernière Synchronisation :** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        "",
        "---",
        "",
        "| Date Début | Titre / Première Requête | Christian | Alix | Note Intégrale | Session ID |",
        "| :--- | :--- | :---: | :---: | :--- | :--- |"
    ]

    for s in reversed(parsed_sessions):
        clean_titre = s['first_line'].replace("|", "-")
        note_link = f"[[{s['filename'].replace('.md', '')}]]"
        idx_lines.append(
            f"| {s['date_display']} | {clean_titre} | {s['nb_christian']} | {s['nb_alix']} | {note_link} | `{s['cid'][:8]}` |"
        )

    try:
        with open(INDEX_FILE, "w", encoding="utf-8") as f_idx:
            f_idx.write("\n".join(idx_lines))
    except Exception as e_idx:
        if verbose:
            print(f"⚠️ Erreur écriture index : {e_idx}")

    # 3. Compilation Table Parquet PyArrow
    if parquet_rows:
        schema = pa.schema([
            ("session_id", pa.string()),
            ("date", pa.string()),
            ("step_index", pa.int64()),
            ("speaker", pa.string()),
            ("content", pa.string()),
            ("char_count", pa.int64())
        ])
        table = pa.Table.from_pylist(parquet_rows, schema=schema)
        pq.write_table(table, PARQUET_FILE, compression="zstd")

    # 4. Sauvegarde de l'état mtime
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f_st:
            json.dump(etat_actuel, f_st, ensure_ascii=False, indent=2)
    except Exception:
        pass

    taille_mo = round(os.path.getsize(PARQUET_FILE) / (1024 * 1024), 2) if PARQUET_FILE.exists() else 0.0

    return {
        "status": "success",
        "sessions_total": len(parsed_sessions),
        "sessions_modifiees": len(sessions_modifiees),
        "md_ecrits": nb_md_ecrits,
        "total_repliques": len(parquet_rows),
        "parquet_taille_mo": taille_mo
    }


if __name__ == "__main__":
    force_run = "--force" in sys.argv
    res = synchroniser_transcriptions_integrales(force=force_run, verbose=True)
    print("=" * 60)
    print("  📜 RÉSULTAT SYNCHRO TRANSCRIPTIONS INTÉGRALES")
    print("=" * 60)
    print(f"  Statut : {res['status']}")
    print(f"  Sessions totales : {res.get('sessions_total', 0)}")
    print(f"  Sessions modifiées : {res.get('sessions_modifiees', 0)}")
    print(f"  Notes Markdown écrites : {res.get('md_ecrits', 0)}")
    print(f"  Répliques Parquet : {res.get('total_repliques', 0):,}")
    print(f"  Taille Parquet : {res.get('parquet_taille_mo', 0.0)} Mo")
    print("=" * 60)


def chercher_transcriptions(terme: str, limite: int = 10, speaker: str = None):
    """Recherche plein-texte ultra-rapide dans la table Parquet de toutes nos discussions."""
    import pyarrow.compute as pc
    if not PARQUET_FILE.exists():
        return []
    try:
        t = pq.read_table(PARQUET_FILE)
        m = pc.match_substring(pc.utf8_lower(t["content"]), terme.lower())
        if speaker:
            m = pc.and_(m, pc.equal(pc.utf8_lower(t["speaker"]), speaker.lower()))
        res = t.filter(m)
        nb = len(res)
        if nb == 0:
            return []
        lignes = []
        indices = range(max(0, nb - limite), nb)
        for i in reversed(indices):
            lignes.append({
                "session_id": res["session_id"][i].as_py(),
                "date": res["date"][i].as_py(),
                "speaker": res["speaker"][i].as_py(),
                "content": res["content"][i].as_py()
            })
        return lignes
    except Exception as e:
        return [{"erreur": str(e)}]
