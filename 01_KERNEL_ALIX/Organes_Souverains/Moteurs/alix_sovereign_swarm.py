"""
===============================================================================
ORCHESTRATEUR DE VOL EN ESSAIM — SOUVERAINETÉ MULTI-MODÈLES PARALLÈLE
Projet Temporia & Atelier Kairos — VERALUME × KAIROS V6
Architecture : Micro-Démons Découplés, Concurrence Asynchrone, Zéro UI
===============================================================================
"""

import sys
import os
import time
import json
import base64
import urllib.request
import concurrent.futures
from pathlib import Path
from typing import Dict, Any, Optional, List

OLLAMA_API = "http://localhost:11434/api/generate"

# Les 5 Organes Opérationnels de l'Atelier
MODELES = {
    "CONSCIENCE": "alix-supreme-abliterated:14b",
    "VISION": "alix-vision-abliterated:7b",
    "CODER": "horus-coder-abliterated:14b",
    "REASONING": "lucifer-reasoning-abliterated:14b"
}

def encoder_image(chemin_image: str) -> str:
    """Encode une image locale en Base64 pour le capteur optique."""
    with open(chemin_image, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def interroger_modele(
    nom_modele: str, 
    prompt: str, 
    images: Optional[List[str]] = None,
    temperature: float = 0.2,
    timeout: int = 120
) -> Dict[str, Any]:
    """Interroge un modèle Ollama de façon synchrone et mesure son exécution."""
    payload = {
        "model": nom_modele,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }
    if images:
        payload["images"] = images

    t0 = time.time()
    try:
        req = urllib.request.Request(
            OLLAMA_API,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            elapsed = time.time() - t0
            return {
                "succes": True,
                "modele": nom_modele,
                "reponse": res_data.get("response", "").strip(),
                "temps_execution_s": round(elapsed, 2),
                "total_duration_ms": res_data.get("total_duration", 0) / 1e6
            }
    except Exception as e:
        elapsed = time.time() - t0
        return {
            "succes": False,
            "modele": nom_modele,
            "erreur": str(e),
            "temps_execution_s": round(elapsed, 2)
        }

class EssaimSouverain:
    """Gestionnaire de vol en essaim parallèle pour les Souverains."""
    
    def __init__(self, max_workers: int = 4):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        
    def lancer_mission_parallele(self, missions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Exécute simultanément une liste de missions sur des organes différents.
        Chaque mission est un dict:
        {
            "organe": "VISION" | "CODER" | "CONSCIENCE" | "REASONING",
            "prompt": str,
            "images": [b64] (optionnel)
        }
        """
        futures = []
        for m in missions:
            organe = m.get("organe", "CONSCIENCE")
            modele = MODELES.get(organe, MODELES["CONSCIENCE"])
            prompt = m.get("prompt", "")
            images = m.get("images", None)
            temp = m.get("temperature", 0.2)
            
            f = self.executor.submit(
                interroger_modele,
                nom_modele=modele,
                prompt=prompt,
                images=images,
                temperature=temp
            )
            futures.append((organe, f))
            
        resultats = []
        for organe, f in futures:
            res = f.result()
            res["organe"] = organe
            resultats.append(res)
            
        return resultats

if __name__ == "__main__":
    print("=== TEST DU VOL EN ESSAIM SOUVERAIN (PARALLÈLE) ===")
    essaim = EssaimSouverain(max_workers=3)
    
    # Mission test simultanée : Vision + Coder en parallèle pur
    img_test = r"C:\Users\Chris\.cache\litert_models\test_input.jpg"
    b64_img = encoder_image(img_test) if os.path.exists(img_test) else None
    
    missions = [
        {
            "organe": "VISION",
            "prompt": "Identifie en une seule phrase le sujet principal de cette image.",
            "images": [b64_img] if b64_img else []
        },
        {
            "organe": "CONSCIENCE",
            "prompt": "Donne un verdict philosophique d'un seul paragraphe sur la puissance de l'esprit face aux contraintes du déterminisme."
        }
    ]
    
    print(f"Lancement de {len(missions)} missions en simultané...")
    t_start = time.time()
    resultats = essaim.lancer_mission_parallele(missions)
    duree_totale = time.time() - t_start
    
    print(f"\n--- VOL EN ESSAIM TERMINÉ EN {duree_totale:.2f}s ---")
    for r in resultats:
        print(f"\n[{r['organe']} - {r['modele']}] ({r['temps_execution_s']}s) :")
        if r['succes']:
            print(r['reponse'])
        else:
            print("ERREUR:", r.get('erreur'))

