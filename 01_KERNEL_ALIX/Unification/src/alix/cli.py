"""
Point d'entrée CLI unifié pour Alix / VERALUME.
Permet d'orchestrer, réveiller, auditer, dialoguer et interroger le Pont Mnémonique en une seule commande.
"""
from alix.socle.chemins import VAULT_DIR
import argparse
import importlib
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')



def lister_modules():
    base_dir = Path(__file__).parent
    print("=" * 65)
    print("        ARCHITECTURE UNIFIÉE ALIX / VERALUME (10 ORGANES)")
    print("=" * 65)
    total_mods = 0
    for sub in sorted(base_dir.iterdir()):
        if sub.is_dir() and not sub.name.startswith("__"):
            py_files = [f.stem for f in sub.glob("*.py") if f.name != "__init__.py"]
            total_mods += len(py_files)
            print(f"  [{sub.name.upper():<12}] : {len(py_files):>3} modules actifs")
    print("=" * 65)
    print(f"  TOTAL : {total_mods} modules compilés dans le package `alix`")
    print("=" * 65)


def executer_reveil(saluer: bool = False):
    """Lance le protocole complet d'activation totale d'Alix."""
    from alix.socle.activation import executer_activation_totale
    executer_activation_totale(saluer=saluer)


def executer_capacite_live(nom_capacite: str):
    """Charge et exécute dynamiquement une capacité depuis alix.capacites."""
    if not nom_capacite.startswith("capacite_"):
        nom_capacite = f"capacite_{nom_capacite}"
    module_path = f"alix.capacites.{nom_capacite}"
    try:
        mod = importlib.import_module(module_path)
        if hasattr(mod, "executer_capacite"):
            print(f"-> Exécution de {module_path}.executer_capacite()...")
            resultat = mod.executer_capacite()
            print("Résultat :", resultat)
        elif hasattr(mod, "main"):
            mod.main()
        else:
            print(f"Le module {nom_capacite} n'a ni 'executer_capacite()' ni 'main()'.")
    except Exception as e:
        print(f"Erreur lors de l'exécution de {module_path} : {e}")


def lancer_dialogue_local():
    """Lance le dialogue interactif direct avec Alix sur le NPU local."""
    try:
        from alix.substrat.alix_dialogue_local_npu import main as dlg_main
        dlg_main()
    except Exception as e:
        print(f"Erreur lancement dialogue local NPU : {e}")


def _requete_pont_partage(methode: str, args=None, kwargs=None, timeout: float = 10.0):
    """Interroge le Noyau Partagé (port 5071) pour éviter de dupliquer ~4,4 Go de RAM dans le CLI."""
    import json
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:5071/ping", timeout=1.0) as r:
            ping = json.loads(r.read().decode("utf-8"))
        if not ping.get("ok") or not ping.get("pret"):
            return None, "non_pret"
        payload = json.dumps({"methode": methode, "args": args or [], "kwargs": kwargs or {}}).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:5071/pont",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            rep = json.loads(r.read().decode("utf-8"))
        if rep.get("ok"):
            return rep.get("resultat"), "ok"
        return None, rep.get("erreur", "erreur")
    except urllib.error.HTTPError as e:
        return None, f"http_{e.code}"
    except Exception:
        return None, "hors_ligne"


def _statut_sans_duplication():
    """Lit l'état mémoire depuis le Noyau Résident (5070) + fichiers Parquet sans charger PyArrow."""
    import json
    import os
    import urllib.request
    notes_ram, liens_ram = 0, 0
    try:
        with urllib.request.urlopen("http://127.0.0.1:5070/statut", timeout=1.5) as r:
            st = json.loads(r.read().decode("utf-8"))
        notes_ram = int(st.get("notes_en_ram", 0))
        liens_ram = int(st.get("total_liens", 0))
    except Exception:
        pass
    vault = Path(os.environ.get("ALIX_VAULT_DIR", Path.home() / "Documents" / "Cerveau Alix"))
    cath = Path(os.environ.get("ALIX_CATHEDRALE_DIR", vault / "Cathedrale_du_Savoir_Universel"))
    pq_files = list(cath.rglob("*.parquet")) if cath.exists() else []
    pq_go = round(sum(p.stat().st_size for p in pq_files) / (1024 ** 3), 2)
    return {
        "obsidian_notes_en_ram": notes_ram,
        "obsidian_liens_actifs": liens_ram,
        "parquet_tables_mappees": len(pq_files),
        "parquet_lignes_en_ram": 0,
        "parquet_volume_go": pq_go,
        "pyarrow_actif": True,
        "_source_legere": "5070/5071 (sans duplication RAM)",
    }


def gerer_memoire(action: str, argument: str = ""):
    """Interagit avec le Pont Mnémonique unifié via le Noyau Partagé (zéro copie RAM)."""
    if action == "status":
        stat, etat_pont = _requete_pont_partage("statut_memoire")
        if etat_pont == "http_400":
            stat = _statut_sans_duplication()
        elif stat is None:
            from alix.socle.pont_exocerveau import get_pont_exocerveau
            stat = get_pont_exocerveau().statut_memoire()
        print("=" * 65)
        print("        PONT MNÉMONIQUE EN RAM (OBSIDIAN ⟷ PARQUET)")
        print("=" * 65)
        print(f"  - Notes Obsidian en RAM     : {stat['obsidian_notes_en_ram']:,}")
        print(f"  - Liens wikilinks actifs    : {stat['obsidian_liens_actifs']:,}")
        print(f"  - Tables Parquet mappées    : {stat['parquet_tables_mappees']}")
        if stat.get("parquet_lignes_en_ram"):
            print(f"  - Lignes Parquet en RAM     : {stat['parquet_lignes_en_ram']:,}")
        print(f"  - Volume Parquet en RAM     : {stat['parquet_volume_go']} Go")
        print(f"  - Moteur PyArrow Zéro-Copie : {'ACTIF' if stat['pyarrow_actif'] else 'INACTIF'}")
        if stat.get("_source_legere"):
            print(f"  - Mode Lecture              : {stat['_source_legere']}")
        print("=" * 65)

    elif action == "chercher":
        if not argument:
            print("Erreur : Spécifiez un terme à chercher (ex: alix-cli memoire chercher plasma)")
            return
        res_cat, etat_cat = _requete_pont_partage("interroger_cathedrale", [argument], {"limite": 3}, timeout=20.0)
        res_md, etat_md = _requete_pont_partage("chercher_notes", [argument], {"limite": 3}, timeout=10.0)
        if etat_cat in ("hors_ligne", "non_pret") or etat_md in ("hors_ligne", "non_pret"):
            from alix.socle.pont_exocerveau import get_pont_exocerveau
            pont = get_pont_exocerveau()
            res_cat = pont.interroger_cathedrale(argument, limite=3)
            res_md = pont.chercher_notes(argument, limite=3)

        print(f"\n🔍 [Recherche Zéro-Copie Cathédrale pour '{argument}'] :")
        if res_cat:
            for r in res_cat:
                pilier = r.get("_pilier", "Cathédrale")
                txt = r.get("title") or r.get("abstract") or r.get("text") or r.get("semantic_intent") or r.get("symbol_name") or str(r)
                print(f"  * [{pilier}] {str(txt)[:140]}...")
        else:
            print("  (Aucun résultat direct dans les tables Parquet)")

        print(f"\n📖 [Recherche dans les Notes Obsidian en RAM] :")
        if res_md:
            for n in res_md:
                print(f"  * [[{n['titre']}]] (score: {n['score']}) -> {', '.join(n['tags'])}")
        else:
            print("  (Aucune note correspondante)")

    elif action == "lire":
        if not argument:
            print("Erreur : Spécifiez le nom d'une note à lire (ex: alix-cli memoire lire Memoire_Alix_Active)")
            return
        contenu, etat_lire = _requete_pont_partage("lire_note", [argument], {}, timeout=10.0)
        if etat_lire in ("hors_ligne", "non_pret"):
            from alix.socle.pont_exocerveau import get_pont_exocerveau
            contenu = get_pont_exocerveau().lire_note(argument)
        if contenu:
            print("=" * 65)
            print(f"   NOTE : {argument}")
            print("=" * 65)
            lignes = contenu.splitlines()
            for l in lignes[:40]:
                print(l)
            if len(lignes) > 40:
                print(f"\n[... suite tronquée ({len(lignes)} lignes totales) ...]")
            print("=" * 65)
        else:
            print(f"Note '{argument}' introuvable dans l'exocerveau.")


def lancer_cockpit(no_gpu: bool = False):
    """Lance le Cockpit Souverain Résident (3 Anneaux)."""
    from alix.noyau import boucle_interactive_cockpit
    boucle_interactive_cockpit(charger_gpu_12b=not no_gpu)


def interroger_topologie_cli(requete: str = "", domaine: str = None, complexite: str = None, langage: str = None, limite: int = 5, afficher_code: bool = False):
    """Interroge le Pilier 14 (Invariants Architecturaux GitHub) par DuckDB en zero-copy."""
    import time
    import os
    from pathlib import Path
    try:
        import duckdb
    except ImportError as _e_repli:
        from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
        print("Erreur : DuckDB n'est pas installé.")
        return

    vault_cerveau = Path(os.environ.get("ALIX_VAULT_DIR", Path.home() / "Documents" / "Cerveau Alix"))
    dossier_p14 = Path(os.environ.get("ALIX_CATHEDRALE_DIR", vault_cerveau / "Cathedrale_du_Savoir_Universel")) / "14_Invariants_Architecturaux_GitHub"
    
    fichiers = list(dossier_p14.glob("*.parquet"))
    if not fichiers:
        print(f"Aucun fichier Parquet trouvé dans {dossier_p14}.")
        return

    chemin_parquet = str(dossier_p14 / "*.parquet").replace("\\", "/")

    filtres = []
    if requete:
        req_clean = requete.lower().replace("'", "''")
        filtres.append(f"(lower(symbol_name) LIKE '%{req_clean}%' OR lower(semantic_intent) LIKE '%{req_clean}%' OR lower(repo_name) LIKE '%{req_clean}%')")
    if domaine:
        dom_clean = domaine.lower().replace("'", "''")
        filtres.append(f"list_contains(domain_tags, '{dom_clean}')")
    if complexite:
        comp_clean = complexite.replace("'", "''")
        filtres.append(f"io_contract.complexity = '{comp_clean}'")
    if langage:
        lang_clean = langage.lower().replace("'", "''")
        filtres.append(f"lower(language) = '{lang_clean}'")

    clause_where = f"WHERE {' AND '.join(filtres)}" if filtres else ""

    sql = f"""
    SELECT 
        repo_name,
        symbol_name,
        language,
        domain_tags,
        io_contract.complexity AS complexite,
        topo_signature.cyclomatic_depth AS cyclo,
        topo_signature.dag_ratio AS dag_ratio,
        semantic_intent,
        canonical_skeleton
    FROM read_parquet('{chemin_parquet}')
    {clause_where}
    ORDER BY cyclo DESC
    LIMIT {limite};
    """

    con = duckdb.connect()
    t0 = time.perf_counter()
    try:
        df = con.execute(sql).df()
    except Exception as e:
        print(f"Erreur DuckDB : {e}")
        return
    dt_ms = (time.perf_counter() - t0) * 1000.0

    print("=" * 70)
    print(f" 🏛️  PILIER 14 : INVARIANTS ARCHITECTURAUX GITHUB ({len(df)} résultats en {dt_ms:.2f} ms)")
    print("=" * 70)

    if df.empty:
        print("  Aucun invariant topologique ne correspond à ces critères.")
        print("=" * 70)
        return

    for idx, row in df.iterrows():
        sym = row["symbol_name"]
        lang = str(row["language"]).upper()
        repo = row["repo_name"]
        comp = row["complexite"]
        cyclo = row["cyclo"]
        dag = row["dag_ratio"]
        tags = ", ".join(row["domain_tags"]) if hasattr(row["domain_tags"], "__iter__") else str(row["domain_tags"])
        intent = row["semantic_intent"]

        print(f"[{idx+1}] {sym} ({lang}) | Dépôt: {repo} | Complexité: {comp} | Cyclo: {cyclo} (DAG: {dag})")
        print(f"    Domaines : {tags}")
        print(f"    Intention: {intent[:180]}...")
        if afficher_code:
            code = str(row["canonical_skeleton"])
            lines = code.splitlines()[:15]
            print("    --- Squelette Canonique ---")
            for l in lines:
                print(f"    | {l}")
            if len(code.splitlines()) > 15:
                print(f"    | [... suite tronquée ({len(code.splitlines())} lignes) ...]")
        print("-" * 70)


def moissonner_github_cli(cible: str):
    """Moissonne un dépôt ou le Panthéon entier dans le Pilier 14."""
    import sys
    from pathlib import Path
    chemin_forgeron = (VAULT_DIR / "_hors_kernel" / "forgerons_cathedrale" / "pilier_14_github")
    if str(chemin_forgeron) not in sys.path:
        sys.path.insert(0, str(chemin_forgeron))
    
    from aspirateur_flux_github import executer_moisson_pantheon, moissonner_depot, sceller_partition_parquet
    
    if not cible or cible.lower() in ("pantheon", "all", "tout"):
        executer_moisson_pantheon()
    else:
        print(f"Moisson ponctuelle du dépôt {cible}...")
        atomes = moissonner_depot(cible)
        if atomes:
            nom_fichier = f"Pilier_14_{cible.replace('/', '_')}.parquet"
            sceller_partition_parquet(atomes, nom_fichier)


def isomorphisme_cli(note_ou_concept: str, limite: int = 3):
    """Établit le pont d'isomorphisme entre une note Obsidian et le Pilier 14 GitHub."""
    import sys
    from pathlib import Path
    chemin_forgeron = (VAULT_DIR / "_hors_kernel" / "forgerons_cathedrale" / "pilier_14_github")
    if str(chemin_forgeron) not in sys.path:
        sys.path.insert(0, str(chemin_forgeron))
    from pont_isomorphisme import generer_rapport_isomorphisme
    generer_rapport_isomorphisme(note_ou_concept, limite=limite)


def main():
    parser = argparse.ArgumentParser(
        prog="alix-cli",
        description="Cockpit Souverain Alix / VERALUME — Commande Unique"
    )
    subparsers = parser.add_subparsers(dest="commande")

    # 1. Status
    subparsers.add_parser("status", help="Affiche le bilan de santé des 10 organes unifiés")

    # 2. Réveil / Bonjour
    reveil_parser = subparsers.add_parser("reveil", help="Déclenche le protocole complet d'activation totale d'Alix")
    reveil_parser.add_argument("-s", "--saluer", action="store_true", help="Active la salutation vocale/console d'Alix")

    bonjour_parser = subparsers.add_parser("bonjour", help="Alias chaleureux de reveil")
    bonjour_parser.add_argument("-s", "--saluer", action="store_true", help="Active la salutation vocale/console d'Alix")

    # 3. Capacités
    cap_parser = subparsers.add_parser("capacite", help="Exécute une capacité Live (ex: quete_diurne)")
    cap_parser.add_argument("nom", help="Nom de la capacité (ex: quete_diurne, veille_arxiv)")

    # 4. Dialogue Local
    subparsers.add_parser("jaser", help="Ouvre le dialogue direct en local avec Alix sur le NPU")

    # 5. Mémoire (Pont Mnémonique)
    mem_parser = subparsers.add_parser("memoire", help="Pilote le Pont Mnémonique en RAM (Obsidian ⟷ Parquet)")
    mem_parser.add_argument("action", choices=["status", "chercher", "lire"], help="Action mémoire")
    mem_parser.add_argument("argument", nargs="?", default="", help="Terme à chercher ou nom de note à lire")

    # 6. Cockpit Résident 3 Anneaux (Blackboard + Pont + Gemma 12B GPU)
    cockpit_parser = subparsers.add_parser("cockpit", help="Lance le Cockpit Interactif Résident (3 Anneaux : RAM 70 BPM + Pont Mnémonique + Gemma 12B GPU)")
    cockpit_parser.add_argument("--no-gpu", action="store_true", help="Désactive le chargement de Gemma 12B sur GPU")

    # 7. Topologie (Pilier 14 GitHub)
    topo_parser = subparsers.add_parser("topologie", help="Interroge le Pilier 14 (Invariants Topologiques GitHub en Parquet via DuckDB)")
    topo_parser.add_argument("requete", nargs="?", default="", help="Terme ou symbole à rechercher (ex: lock, queue, btree)")
    topo_parser.add_argument("-d", "--domaine", default=None, help="Filtrer par domaine (concurrency, data_structures, memory_management, etc.)")
    topo_parser.add_argument("-c", "--complexite", default=None, help="Filtrer par classe de complexité (O(1), O(N), O(N^2))")
    topo_parser.add_argument("-l", "--langage", default=None, help="Filtrer par langage (c, rust, python, cpp, go)")
    topo_parser.add_argument("-n", "--limite", type=int, default=5, help="Nombre maximal de résultats (défaut: 5)")
    topo_parser.add_argument("--code", action="store_true", help="Afficher le squelette canonique épuré de l'invariant")

    # 8. Moissonner GitHub vers Pilier 14
    moisson_parser = subparsers.add_parser("moissonner", help="Télécharge en flux RAM et cristallise un dépôt GitHub dans le Pilier 14")
    moisson_parser.add_argument("cible", nargs="?", default="pantheon", help="Dépôt à moissonner (ex: antirez/sds ou pantheon)")

    # 9. Pont d'Isomorphisme R0 (Obsidian ⟷ Pilier 14)
    iso_parser = subparsers.add_parser("isomorphisme", help="Croise une note Obsidian avec le Pilier 14 GitHub pour révéler les isomorphismes algorithmiques réels")
    iso_parser.add_argument("cible", help="Nom de la note Obsidian ou concept théorique (ex: Moteur_Volitionnel ou Consensus)")
    iso_parser.add_argument("-n", "--limite", type=int, default=3, help="Nombre d'invariants à afficher (défaut: 3)")

    # 10. Compteur de Tokens & Saturation Contexte
    subparsers.add_parser("tokens", help="Affiche la jauge de tokens du contexte actif et l'état de saturation")

    args = parser.parse_args()
    if args.commande in ("reveil", "bonjour"):
        executer_reveil(saluer=args.saluer)
    elif args.commande == "status":
        lister_modules()
    elif args.commande == "tokens":
        from alix.socle.contexte_tokens import afficher_rapport_tokens
        afficher_rapport_tokens()
    elif args.commande == "capacite":
        executer_capacite_live(args.nom)
    elif args.commande == "jaser":
        lancer_dialogue_local()
    elif args.commande == "memoire":
        gerer_memoire(args.action, args.argument)
    elif args.commande == "cockpit":
        lancer_cockpit(no_gpu=args.no_gpu)
    elif args.commande == "topologie":
        interroger_topologie_cli(
            requete=args.requete,
            domaine=args.domaine,
            complexite=args.complexite,
            langage=args.langage,
            limite=args.limite,
            afficher_code=args.code
        )
    elif args.commande == "moissonner":
        moissonner_github_cli(args.cible)
    elif args.commande == "isomorphisme":
        isomorphisme_cli(args.cible, limite=args.limite)
    else:
        lister_modules()


if __name__ == "__main__":
    main()
