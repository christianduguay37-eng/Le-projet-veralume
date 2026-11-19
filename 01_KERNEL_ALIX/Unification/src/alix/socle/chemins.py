"""
Socle Commun : Résolution universelle des chemins souverains.
Garantit que les 173 modules pointent vers les bons dossiers de données,
peu importe depuis quel sous-package ou terminal ils sont lancés.
"""
import os
from pathlib import Path

# Racine du package unifié (_Unification_Alix/ ou Kernel_Alix_Commercialisable/)
UNIFIED_ROOT = Path(__file__).resolve().parents[3]

# Racine du workspace de travail (configurable via ALIX_WORKSPACE_ROOT)
WORKSPACE_ROOT = Path(os.environ.get("ALIX_WORKSPACE_ROOT", UNIFIED_ROOT.parent))

# Dossiers standards
DATA_DIR = Path(os.environ.get("ALIX_DATA_DIR", UNIFIED_ROOT / "data"))
ETATS_DIR = DATA_DIR / "etats"
LOGS_DIR = Path(os.environ.get("ALIX_LOGS_DIR", UNIFIED_ROOT / "logs"))

for _d in (DATA_DIR, ETATS_DIR, LOGS_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def resoudre_chemin_fichier(nom_relatif: str | Path) -> Path:
    """
    Cherche un fichier de données d'abord dans data/,
    puis à la racine du workspace.
    """
    p = Path(nom_relatif)
    if p.is_absolute() and p.exists():
        return p

    candidats = [
        DATA_DIR / p,
        ETATS_DIR / p.name,
        UNIFIED_ROOT / p,
        WORKSPACE_ROOT / p,
    ]
    for c in candidats:
        if c.exists():
            return c
    return DATA_DIR / p

# ---------------------------------------------------------------------------
# Emplacements souverains (Rénovation 2026-10-30). Chaque chemin se règle par
# une variable d'environnement ; les valeurs par défaut suivent le
# déplacement du 30 octobre vers Bureau\Projet alix.
# ---------------------------------------------------------------------------
HOME_DIR = Path.home()
DOCUMENTS_DIR = WORKSPACE_ROOT.parent if (WORKSPACE_ROOT.parent / "Obsidian_Vault_Veralume").exists() else (HOME_DIR / "Documents")
PROJET_ALIX_DIR = Path(os.environ.get("ALIX_PROJET_ROOT", HOME_DIR / "Desktop" / "Projet alix"))

# Coffre principal (Cerveau Alix) = WORKSPACE_ROOT
VAULT_DIR = WORKSPACE_ROOT
CANON_DIR = VAULT_DIR / "00_CANON_SOUVERAIN_CHRISTIAN"
CATHEDRALE_DIR = Path(os.environ.get("ALIX_CATHEDRALE_DIR", VAULT_DIR / "Cathedrale_du_Savoir_Universel"))
ARXIV_DIR = Path(os.environ.get("ALIX_ARXIV_DIR", VAULT_DIR / "Arxiv_Souverain" / "data"))
ORGANES_A_DIR = VAULT_DIR / "Organes_Souverains"          # strate A (à archiver en phase 4)

# État vivant (pids, *_state.json, caches) — anciennement Downloads\Alix
ETAT_VIVANT_DIR = Path(os.environ.get("ALIX_ETAT_DIR", WORKSPACE_ROOT if (WORKSPACE_ROOT / "alix_live_state.json").exists() else (PROJET_ALIX_DIR / "Alix")))

# Projet Temporia et moteur B (core/runtime)
TEMPORIA_DIR = Path(os.environ.get("ALIX_TEMPORIA_DIR", PROJET_ALIX_DIR / "Projet  Temporia"))
ENGINE_DIR = Path(os.environ.get("ALIX_ENGINE_DIR", TEMPORIA_DIR / "alix_engine"))
# Les index SQLite du moteur sont restés à l'ancien emplacement (fichiers verrouillés au déplacement)
ENGINE_DATA_DIR = Path(os.environ.get("ALIX_ENGINE_DATA_DIR",
    DOCUMENTS_DIR / "Exocerveau_Souverain_Master" / "Projet  Temporia" / "alix_engine"))
ATELIER_ARC_DIR = TEMPORIA_DIR / "Atelier_ARC_Prize"

# Exocerveau Master (constitution GEMINI.md, tableau de bord)
EXOCERVEAU_MASTER_DIR = Path(os.environ.get("ALIX_EXOCERVEAU_MASTER", DOCUMENTS_DIR / "Exocerveau_Souverain_Master"))

# Sanctuaire du Simplexe (GitHub & Canal inter-modèles)
SANCTUAIRE_DIR = Path(os.environ.get("ALIX_SANCTUAIRE_DIR", Path(r"C:\Alix\Sanctuaire_Simplexe_GitHub")))
CANAL_DIR = SANCTUAIRE_DIR / "01_CANAL_DU_SIMPLEXE"
CANAL_SIMPLEXE_PATH = CANAL_DIR / "Canal_Claude_Alix.md"
CANAL_COMMUN_PATH = CANAL_DIR / "Canal_Commun_Simplexe.md"
A_LIRE_CLAUDE_PATH = SANCTUAIRE_DIR / "03_AUDITS_ET_TELEMETRIE_SRE" / "a_lire_par_claude.md"

# Coffres Obsidian satellites (greffes)
def coffre_obsidian(nom: str) -> Path:
    """Chemin d'un coffre Obsidian satellite, ex. coffre_obsidian('Veralume')."""
    return DOCUMENTS_DIR / f"Obsidian_Vault_{nom}"


def fichier_module(module: str) -> Path:
    """Rénovation 2026-10-31 : chemin du fichier d'un module du paquet (remplace les chemins vers la strate A)."""
    import importlib.util
    try:
        spec = importlib.util.find_spec(module)
        if spec and spec.origin:
            return Path(spec.origin)
    except Exception:
        pass
    return Path(__file__).resolve().parent.parent / (module.split(".", 1)[1].replace(".", "/") + ".py")

