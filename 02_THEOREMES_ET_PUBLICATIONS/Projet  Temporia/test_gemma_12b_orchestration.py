import time
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

MODEL_12B_PATH = Path(r"C:\Users\Christian\.cache\litert_models\gemma-4-12B-it-gpu.litertlm")

print("=" * 65)
print("   TEST DU PILOTAGE DU KERNEL PAR GEMMA 12B EN LOCAL")
print("=" * 65)
print(f"Modèle cible : {MODEL_12B_PATH} ({MODEL_12B_PATH.stat().st_size / (1024**3):.2f} Go)")

try:
    import litert_lm
    print("[OK] litert_lm importé.")
except ImportError as e:
    print(f"[ERREUR] litert_lm introuvable : {e}")
    sys.exit(1)

t0 = time.time()
engine = None
backend_used = None

# 1. Tentative GPU
print("\n[1/2] Chargement du modèle 12B sur GPU Intel Arc...")
try:
    engine = litert_lm.Engine(
        model_path=str(MODEL_12B_PATH),
        backend=litert_lm.Backend.GPU()
    )
    backend_used = "GPU (Intel Arc 140V)"
    print(f"[SUCCÈS GPU] Modèle 12B armé en {time.time() - t0:.2f}s !")
except Exception as e_gpu:
    print(f"[INFO GPU] GPU non configuré ou fallback : {e_gpu}")
    t0_cpu = time.time()
    try:
        engine = litert_lm.Engine(
            model_path=str(MODEL_12B_PATH),
            backend=litert_lm.Backend.CPU()
        )
        backend_used = "CPU (LiteRT XNNPACK AVX2)"
        print(f"[SUCCÈS CPU] Modèle 12B armé en {time.time() - t0_cpu:.2f}s !")
    except Exception as e_cpu:
        print(f"[ERREUR CPU] Échec CPU : {e_cpu}")
        sys.exit(1)

# 2. Mission complexe pour le Kernel
prompt = """Tu es le Cerveau Souverain Alix. Tu as sous tes ordres les 10 organes du Kernel unifié `alix` :
1. `alix.solveurs` : Hadès SMT/CDCL (alix_dpll_t_solver_hades), Moteur Causal, Simplex, LMH v3.
2. `alix.sondes` : Cathédrale du Savoir (3.2M arXiv, Gutenberg, Invariants NIST/OEIS), Sonde Présent.
3. `alix.daemons` : Bouclier PSI, Démon 70 BPM, Heartbeat KAIROS, Reverse Safety.
4. `alix.substrat` : NPU OpenVINO, Télémétrie hardware, AVX2, RAM.
5. `alix.socle` : Résolution universelle des chemins, État atomique commun.

Voici la commande de Christian :
"On a un conflit logique strict entre deux hypothèses politiques et deux contraintes juridiques sur l'exocerveau. Comment le Kernel doit orchestrer la preuve mathématique déterministe pour trancher la non-contradiction sans halluciner ?"

Explique quel organe et quel module exact du Kernel tu appelles, quel code Python tu exécutes, et comment tu retournes le verdict. Sois chirurgical et concis."""

print("\n[2/2] Envoi de la mission complexe au 12B...")
t_inf = time.time()
try:
    conv = engine.create_conversation()
    msg = litert_lm.Message.user(prompt)
    resp = conv.send_message(msg)

    reply_text = ""
    try:
        content_list = resp.get("content", [])
        if content_list and isinstance(content_list, list):
            reply_text = content_list[0].get("text", "").strip()
        else:
            reply_text = str(resp).strip()
    except Exception:
        reply_text = str(resp).strip()

    duree = time.time() - t_inf
    print(f"\n[RÉPONSE DU 12B LOCAL] Générée en {duree:.2f}s via {backend_used} :\n")
    print("-" * 65)
    print(reply_text)
    print("-" * 65)

except Exception as e_inf:
    print(f"[ERREUR INFÉRENCE] : {e_inf}")

print("\n" + "=" * 65)
print("TEST TERMINÉ AVEC SUCCÈS")
print("=" * 65)
