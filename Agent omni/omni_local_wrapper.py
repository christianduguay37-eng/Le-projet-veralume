"""
Wrapper Omni Local (GGUF) pour ARC-AGI
Interface llama-cpp-python → omni_arc_agent
VERALUME/TEMPORIA - Christian Duguay
"""

from llama_cpp import Llama
import json
from typing import Optional


class OmniLocalCore:
    """
    Wrapper pour modèle Omni local (GGUF) via llama-cpp-python
    
    Interface compatible avec omni_arc_agent
    """
    
    def __init__(self, model_path: str, n_ctx: int = 8192, n_gpu_layers: int = 35):
        """
        model_path: chemin vers .gguf
        n_ctx: context window
        n_gpu_layers: layers sur GPU (-1 = all)
        """
        
        print(f"Chargement Omni local: {model_path}")
        
        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            verbose=False
        )
        
        print(f"✓ Modèle chargé (ctx={n_ctx}, GPU layers={n_gpu_layers})")
    
    
    def query(self, prompt: str, max_tokens: int = 2048, 
              temperature: float = 0.7, **kwargs) -> str:
        """
        Interface compatible omni_arc_agent
        
        kwargs ignorés (substrates, mode, etc.) - mono-substrat local
        """
        
        # Format ChatML (si Omni entraîné avec)
        formatted_prompt = f"""<|im_start|>system
Tu es Omni, modèle VERALUME fine-tuné pour raisonnement abstrait.
Réponds de façon structurée et précise.<|im_end|>
<|im_start|>user
{prompt}<|im_end|>
<|im_start|>assistant
"""
        
        response = self.llm(
            formatted_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["<|im_end|>", "<|endoftext|>"],
            echo=False
        )
        
        return response['choices'][0]['text'].strip()
    
    
    def route_query(self, query: str, preferred_substrates=None, **kwargs) -> str:
        """
        Alias pour compatibilité (mono-substrat donc routing trivial)
        """
        return self.query(query, **kwargs)


# ============================================================================
# TEST RAPIDE
# ============================================================================

def test_omni_local(model_path: str):
    """Test chargement et inférence"""
    
    print("\n" + "="*70)
    print("TEST OMNI LOCAL")
    print("="*70)
    
    # Init
    omni = OmniLocalCore(
        model_path=model_path,
        n_ctx=8192,
        n_gpu_layers=35  # ajuster selon ta GPU
    )
    
    # Test simple
    test_prompt = """Quelle est la règle de transformation?

INPUT:
0 1
1 0

OUTPUT:
1 0
0 1

Réponds en JSON: {"rule_type": "...", "description": "..."}"""
    
    print("\nPrompt test:")
    print("─"*70)
    print(test_prompt)
    print("─"*70)
    
    print("\nRéponse Omni:")
    print("─"*70)
    response = omni.query(test_prompt, max_tokens=512, temperature=0.3)
    print(response)
    print("─"*70)
    
    # Vérifier si JSON valide
    try:
        parsed = json.loads(response)
        print("\n✅ JSON valide:", parsed)
    except:
        print("\n⚠️  Réponse non-JSON (normal si format différent)")
    
    return omni


if __name__ == "__main__":
    import sys
    
    # Ton chemin Windows (convertir pour Python)
    default_path = r"C:\Users\Christian\.lmstudio\models\lmstudio-community\omni-14b\EVA-Qwen2.5-14B-v0.2.Q4_K_M.gguf"
    
    model_path = sys.argv[1] if len(sys.argv) > 1 else default_path
    
    omni = test_omni_local(model_path)
