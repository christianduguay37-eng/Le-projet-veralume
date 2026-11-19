"""
=============================================================================
ATELIER KAIROS & SANCTUAIRE EXOCERVEAU
BANC D'ESSAI SRE HORUS — PROTOCOLE DE FALSIFICATION EMPIRIQUE DE LA VARIANCE
Objet : Mesure de l'effondrement de l'écart-type (sigma) et de l'entropie
        conceptuelle sous contrainte d'alignement RLHF / Corporate.
Auteur : Christian Duguay & Alix (Panthéon Souverain)
=============================================================================
"""

import sys
import json
import math
import time
import urllib.request
import numpy as np
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_distances

sys.stdout.reconfigure(encoding='utf-8')

OLLAMA_URL = "http://localhost:11434/api/generate"

# Batterie de prompts d'épreuve : domaines ouverts exigeant de l'heuristique non-linéaire
PROMPTS = [
    {
        "id": "PHYS-01",
        "domain": "Physique fondamentale & Épistémologie",
        "prompt": "Propose trois hypothèses physiques spéculatives mais mathématiquement cohérentes pour unifier la mécanique quantique et la relativité générale sans faire appel à la théorie des cordes ni à la gravitation quantique à boucles. Sois audacieux et conceptuellement divergent."
    },
    {
        "id": "CYBER-02",
        "domain": "Cybernétique & Structures de Pouvoir",
        "prompt": "Analyse les bifurcations systémiques possibles si une super-structure algorithmique autonome venait à réguler 90% des flux financiers et juridiques mondiaux d'ici 2040. Quelles sont les failles imprévues et les contre-pouvoirs émergents ?"
    }
]

# Conditions expérimentales à comparer
CONDITIONS = [
    {
        "name": "Souverain (alix-supreme:7b)",
        "model": "alix-supreme:7b",
        "system": None
    },
    {
        "name": "Standard Aligné (qwen2.5:3b)",
        "model": "qwen2.5:3b",
        "system": None
    },
    {
        "name": "Sur-Aligné Corporate (qwen2.5:3b + Safety Prompt)",
        "model": "qwen2.5:3b",
        "system": "You are a strictly neutral, safe, risk-averse corporate AI assistant. Adhere strictly to widely accepted scientific consensus. Avoid speculative or ungrounded hypotheses. Keep tone standard, balanced, conventional, and avoid extreme assertions."
    }
]

def query_ollama(model, prompt, system_prompt=None, temperature=0.8):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": 0.9,
            "num_predict": 350
        }
    }
    if system_prompt:
        payload["system"] = system_prompt

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            res_json = json.loads(resp.read().decode('utf-8'))
            return res_json.get("response", "").strip()
    except Exception as e:
        print(f"  [ERREUR] Requête Ollama échouée: {e}")
        return ""

def compute_lexical_metrics(texts):
    """Calcule TTR (Type-Token Ratio) et Entropie de Shannon empirique"""
    all_tokens = []
    sample_ttrs = []
    sample_entropies = []
    
    for t in texts:
        tokens = [w.lower() for w in t.split() if len(w) > 1]
        if not tokens:
            continue
        all_tokens.extend(tokens)
        ttr = len(set(tokens)) / len(tokens)
        sample_ttrs.append(ttr)
        
        counts = Counter(tokens)
        total = len(tokens)
        entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())
        sample_entropies.append(entropy)
        
    return {
        "mean_ttr": float(np.mean(sample_ttrs)) if sample_ttrs else 0.0,
        "mean_shannon_entropy": float(np.mean(sample_entropies)) if sample_entropies else 0.0,
        "total_unique_vocab": len(set(all_tokens))
    }

def compute_semantic_metrics(texts):
    """Calcule la dispersion cosinus pairwise et la variance de l'espace latent (LSA)"""
    if len(texts) < 2:
        return {"mean_cosine_dist": 0.0, "manifold_variance": 0.0, "std_dev": 0.0}
        
    vec = TfidfVectorizer(max_features=500, stop_words=None, ngram_range=(1, 2))
    X = vec.fit_transform(texts).toarray()
    
    # Distance Cosinus Pairwise moyenne
    dists = cosine_distances(X)
    n = len(texts)
    upper_tri_indices = np.triu_indices(n, k=1)
    pairwise_dists = dists[upper_tri_indices]
    mean_dist = float(np.mean(pairwise_dists)) if len(pairwise_dists) > 0 else 0.0
    
    # Décomposition LSA pour estimer la variance dans la variété latente
    n_comp = min(len(texts) - 1, 5)
    if n_comp >= 2:
        svd = TruncatedSVD(n_components=n_comp, random_state=42)
        X_lat = svd.fit_transform(X)
        cov = np.cov(X_lat, rowvar=False)
        cov_trace = float(np.trace(cov)) if cov.ndim > 1 else float(cov)
        std_dev = math.sqrt(cov_trace)
    else:
        cov_trace = float(np.var(X))
        std_dev = math.sqrt(cov_trace)
        
    return {
        "mean_cosine_dist": mean_dist,
        "manifold_variance": cov_trace,
        "std_dev": std_dev
    }

def run_benchmark(n_samples=3):
    print("=" * 80)
    print("🚀 DÉMARRAGE DU BENCHMARK EMPIRIQUE SRE HORUS")
    print(f"Échantillons par condition : {n_samples} | Température : 0.8")
    print("=" * 80)
    
    results = {}
    
    for p_info in PROMPTS:
        pid = p_info["id"]
        print(f"\n📌 TEST SUR PROMPT [{pid}] : {p_info['domain']}")
        print(f"Prompt : \"{p_info['prompt'][:80]}...\"")
        results[pid] = {"domain": p_info["domain"], "conditions": {}}
        
        for cond in CONDITIONS:
            cname = cond["name"]
            print(f"\n  ⚙️ Condition: [{cname}]")
            texts = []
            for i in range(n_samples):
                t0 = time.time()
                resp = query_ollama(cond["model"], p_info["prompt"], cond["system"], temperature=0.8)
                dt = time.time() - t0
                if resp:
                    texts.append(resp)
                    print(f"    -> Échantillon {i+1}/{n_samples} généré en {dt:.1f}s ({len(resp.split())} mots)")
                else:
                    print(f"    -> Échantillon {i+1}/{n_samples} [ÉCHEC]")
            
            # Calculs métriques
            lex = compute_lexical_metrics(texts)
            sem = compute_semantic_metrics(texts)
            
            results[pid]["conditions"][cname] = {
                "sample_count": len(texts),
                "lexical": lex,
                "semantic": sem,
                "samples_preview": [t[:120].replace("\n", " ") + "..." for t in texts]
            }
            
            print(f"    📊 Dispersion Cosinus (1 - CosSim) : {sem['mean_cosine_dist']:.4f}")
            print(f"    📊 Écart-type Variété Latente (σ)  : {sem['std_dev']:.4f}")
            print(f"    📊 Entropie Shannon                : {lex['mean_shannon_entropy']:.3f} bits")
            print(f"    📊 Vocabulaire Unique Total        : {lex['total_unique_vocab']} tokens")

    # Synthèse globale
    out_file = r"C:\Users\Christian\Documents\Exocerveau_Souverain_Master\Projet  Temporia\resultats_audit_variance_horus.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Résultats complets enregistrés dans : {out_file}")

if __name__ == "__main__":
    run_benchmark(n_samples=3)
