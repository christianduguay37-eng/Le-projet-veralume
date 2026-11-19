"""Package Unifié Alix / VERALUME."""
__version__ = "1.0.0"

# Couche 2, point 3, étape B (Claude & Alix, 2026-11-02) : imports paresseux.
# Avant, toucher au paquet (même `import alix.socle.chemins`) chargeait alix.noyau et tout ce qu'il tire
# (numpy, pyarrow, solveurs) : mesuré +279 Mo privés par petit démon, contre +3 Mo sans.
# `from alix import NoyauSouverain` fonctionne toujours : le nom est chargé au premier accès.
_PARESSEUX = {
    "NoyauSouverain": "alix.noyau",
    "BlackboardRAM": "alix.noyau",
    "boucle_interactive_cockpit": "alix.noyau",
    "AdaptateurLLMUniversel": "alix.socle.adaptateur_llm",
}


def __getattr__(nom):
    module = _PARESSEUX.get(nom)
    if module is None:
        raise AttributeError(f"module 'alix' has no attribute {nom!r}")
    import importlib
    valeur = getattr(importlib.import_module(module), nom)
    globals()[nom] = valeur
    return valeur


def __dir__():
    return sorted(list(globals()) + list(_PARESSEUX))
