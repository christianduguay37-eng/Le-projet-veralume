# -*- coding: utf-8 -*-
"""
================================================================================
          SONDE D'ACTUALITÉ — « Qu'est-ce qui se passe MAINTENANT ? »
================================================================================
Interroge Google News RSS (fr-CA) sur un sujet, fenêtre récente, sans clé API.
Chaque manchette sort avec sa date de publication et son âge en heures.

Usage :
  python alix_sonde_actualite.py "élections Québec Granby"
  python alix_sonde_actualite.py "Lunar Lake NPU" --jours 7 --max 15 --langue en
================================================================================
"""
from alix.socle.chemins import VAULT_DIR
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CACHE = (VAULT_DIR / "Present" / "actualite")


def sonder(sujet: str, jours: int = 2, maxi: int = 10, langue: str = "fr") -> dict:
    if langue == "fr":
        hl, gl, ceid = "fr-CA", "CA", "CA:fr"
    else:
        hl, gl, ceid = "en-CA", "CA", "CA:en"
    q = urllib.parse.quote(f"{sujet} when:{jours}d")
    url = f"https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Alix-Sonde"})
    maintenant = datetime.now(timezone.utc)
    resultat = {
        "sujet": sujet,
        "sonde_a": datetime.now().astimezone().isoformat(timespec="seconds"),
        "fenetre_jours": jours,
        "source": url,
        "manchettes": [],
    }
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            racine = ET.fromstring(r.read())
    except Exception as e:
        resultat["erreur"] = str(e)
        return resultat

    for item in racine.iter("item"):
        titre = item.findtext("title", "")
        src = item.find("source")
        pub = item.findtext("pubDate", "")
        try:
            dt = parsedate_to_datetime(pub)
            age_h = round((maintenant - dt).total_seconds() / 3600, 1)
            pub_local = dt.astimezone().isoformat(timespec="minutes")
        except Exception:
            age_h, pub_local = None, pub
        resultat["manchettes"].append({
            "titre": titre,
            "media": src.text if src is not None else "",
            "publie": pub_local,
            "age_heures": age_h,
            "lien": item.findtext("link", ""),
        })
    resultat["manchettes"].sort(key=lambda m: m["age_heures"] if m["age_heures"] is not None else 1e9)
    resultat["manchettes"] = resultat["manchettes"][:maxi]

    CACHE.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "_", sujet.lower())[:60].strip("_") or "sujet"
    (CACHE / f"{slug}.json").write_text(json.dumps(resultat, ensure_ascii=False, indent=2), encoding="utf-8")
    return resultat


def afficher(r: dict):
    print(f"\n📰 [SONDE ACTUALITÉ] « {r['sujet']} » — sondé à {r['sonde_a']} (fenêtre {r['fenetre_jours']} j)")
    print("=" * 74)
    if r.get("erreur"):
        print(f"❌ Réseau indisponible : {r['erreur']}")
        return
    if not r["manchettes"]:
        print("∅ Aucune manchette récente. Élargir --jours ou reformuler le sujet.")
        return
    for i, m in enumerate(r["manchettes"], 1):
        age = f"{m['age_heures']} h" if m["age_heures"] is not None else "?"
        print(f"[{i:2}] ({age:>7}) {m['titre']}")
        print(f"      {m['media']} · {m['publie']}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("sujet")
    p.add_argument("--jours", type=int, default=2)
    p.add_argument("--max", type=int, default=10)
    p.add_argument("--langue", default="fr", choices=["fr", "en"])
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    res = sonder(a.sujet, a.jours, a.max, a.langue)
    print(json.dumps(res, ensure_ascii=False, indent=2)) if a.json else afficher(res)
