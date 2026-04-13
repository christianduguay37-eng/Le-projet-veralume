"""
Wrapper LM Studio API pour ARC-AGI
Alternative à llama-cpp-python (pas besoin de compiler)
VERALUME/TEMPORIA - Christian Duguay
"""

import requests
import json
from typing import Optional


class OmniLMStudioCore:
    """
    Wrapper pour Omni via LM Studio local server
    
    Plus simple que llama-cpp-python - pas de compilation
    """
    
    def __init__(self, base_url: str = "http://localhost:1234/v1"):
        """
        base_url: URL serveur LM Studio (défaut: http://localhost:1234/v1)
        """
        
        self.base_url = base_url
        self.endpoint = f"{base_url}/chat/completions"
        
        print(f"Connexion LM Studio: {base_url}")
        
        # Test connexion
        try:
            response = requests.get(f"{base_url}/models", timeout=2)
            if response.status_code == 200:
                models = response.json().get('data', [])
                if models:
                    print(f"✓ Connecté - {len(models)} modèle(s) disponible(s)")
                else:
                    print("⚠️  Serveur accessible mais aucun modèle chargé")
            else:
                print(f"⚠️  Serveur répond avec status {response.status_code}")
        except requests.exceptions.RequestException:
            print("❌ Serveur LM Studio non accessible")
            print("   → Lance LM Studio et charge ton modèle Omni")
            print("   → Démarre le serveur local (onglet 'Local Server')")
    
    
    def query(self, prompt: str, max_tokens: int = 2048, 
              temperature: float = 0.7, **kwargs) -> str:
        """
        Interface compatible omni_arc_agent
        """
        
        # Format OpenAI-compatible (LM Studio)
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "Tu es Omni, modèle VERALUME fine-tuné pour raisonnement abstrait. Réponds de façon structurée et précise."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                timeout=120  # 2 min max
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                print(f"❌ Erreur API: {response.status_code}")
                print(response.text)
                return ""
                
        except requests.exceptions.Timeout:
            print("❌ Timeout - requête trop longue (>2 min)")
            return ""
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return ""
    
    
    def route_query(self, query: str, preferred_substrates=None, **kwargs) -> str:
        """
        Alias pour compatibilité (mono-substrat donc routing trivial)
        """
        return self.query(query, **kwargs)


# ============================================================================
# TEST RAPIDE
# ============================================================================

def test_lmstudio_connection():
    """Test connexion LM Studio"""
    
    print("\n" + "="*70)
    print("TEST CONNEXION LM STUDIO")
    print("="*70)
    
    # Init
    omni = OmniLMStudioCore()
    
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
    if response:
        print(response)
        print("─"*70)
        
        # Vérifier si JSON valide
        try:
            parsed = json.loads(response)
            print("\n✅ JSON valide:", parsed)
        except:
            print("\n⚠️  Réponse non-JSON (normal si format différent)")
    else:
        print("Pas de réponse")
        print("─"*70)
    
    return omni


if __name__ == "__main__":
    omni = test_lmstudio_connection()
