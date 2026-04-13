"""
Setup et vérification installation ARC-AGI
VERALUME/TEMPORIA - Christian Duguay
"""

import os
import sys

REQUIRED_FILES = [
    'arc_parser.py',
    'omni_arc_agent.py',
    'omni_lmstudio_wrapper.py',
    'test_lmstudio_arc.py',
    'download_arc_dataset.py'
]

OPTIONAL_FILES = [
    'GUIDE_LMSTUDIO.md',
    'arc_benchmark.py',
    'test_arc_protocol.py'
]


def check_files():
    """Vérifie présence fichiers requis"""
    
    print("="*70)
    print("VÉRIFICATION INSTALLATION ARC-AGI")
    print("="*70)
    
    current_dir = os.getcwd()
    print(f"\nRépertoire: {current_dir}\n")
    
    missing = []
    present = []
    
    print("Fichiers requis:")
    for filename in REQUIRED_FILES:
        if os.path.exists(filename):
            print(f"  ✓ {filename}")
            present.append(filename)
        else:
            print(f"  ✗ {filename} MANQUANT")
            missing.append(filename)
    
    print("\nFichiers optionnels:")
    for filename in OPTIONAL_FILES:
        if os.path.exists(filename):
            print(f"  ✓ {filename}")
        else:
            print(f"  - {filename}")
    
    if missing:
        print("\n" + "="*70)
        print("❌ INSTALLATION INCOMPLÈTE")
        print("="*70)
        print(f"\nFichiers manquants: {len(missing)}")
        for f in missing:
            print(f"  - {f}")
        
        print("\n📥 TÉLÉCHARGE ces fichiers depuis les outputs:")
        for f in missing:
            print(f"  {f}")
        
        print("\n💡 Ou copie-les tous dans:")
        print(f"  {current_dir}")
        
        return False
    else:
        print("\n" + "="*70)
        print("✅ INSTALLATION COMPLÈTE")
        print("="*70)
        print("\nTous les fichiers requis sont présents!")
        return True


def check_dataset():
    """Vérifie présence dataset ARC"""
    
    print("\n" + "="*70)
    print("VÉRIFICATION DATASET ARC")
    print("="*70)
    
    if os.path.exists('arc_data'):
        print("\n✓ Répertoire arc_data/ existe")
        
        if os.path.exists('arc_data/training.json'):
            print("✓ Dataset training.json présent")
            return True
        else:
            print("✗ Dataset training.json manquant")
            print("\n📥 Télécharge le dataset:")
            print("  python download_arc_dataset.py")
            return False
    else:
        print("\n✗ Répertoire arc_data/ manquant")
        print("\n📥 Télécharge le dataset:")
        print("  python download_arc_dataset.py")
        return False


def check_lmstudio():
    """Vérifie connexion LM Studio"""
    
    print("\n" + "="*70)
    print("VÉRIFICATION LM STUDIO")
    print("="*70)
    
    try:
        import requests
        
        try:
            response = requests.get("http://localhost:1234/v1/models", timeout=2)
            if response.status_code == 200:
                models = response.json().get('data', [])
                print("\n✓ LM Studio serveur accessible")
                if models:
                    print(f"✓ {len(models)} modèle(s) chargé(s)")
                    return True
                else:
                    print("⚠️  Serveur actif mais aucun modèle chargé")
                    print("\n📋 Dans LM Studio:")
                    print("  1. Charge ton modèle EVA-Qwen2.5-14B")
                    return False
            else:
                print(f"\n⚠️  Serveur répond mais status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException:
            print("\n✗ LM Studio serveur non accessible")
            print("\n📋 Lance LM Studio et:")
            print("  1. Charge ton modèle EVA-Qwen2.5-14B")
            print("  2. Va dans Developer/Local Server")
            print("  3. Clique 'Start Server'")
            return False
            
    except ImportError:
        print("\n✗ Module 'requests' manquant")
        print("\n📥 Installe:")
        print("  pip install requests")
        return False


def print_next_steps(files_ok, dataset_ok, lmstudio_ok):
    """Affiche prochaines étapes"""
    
    print("\n" + "="*70)
    print("PROCHAINES ÉTAPES")
    print("="*70)
    
    if not files_ok:
        print("\n1️⃣ Télécharge tous les fichiers manquants")
        print("2️⃣ Place-les dans le répertoire actuel")
        print("3️⃣ Relance ce script: python setup_check.py")
        return
    
    if not dataset_ok:
        print("\n1️⃣ Télécharge le dataset ARC:")
        print("     python download_arc_dataset.py")
        print("2️⃣ Relance ce script: python setup_check.py")
        return
    
    if not lmstudio_ok:
        print("\n1️⃣ Lance LM Studio")
        print("2️⃣ Charge ton modèle EVA-Qwen2.5-14B")
        print("3️⃣ Démarre le serveur local")
        print("4️⃣ Relance ce script: python setup_check.py")
        return
    
    # Tout OK
    print("\n🎉 SETUP COMPLET!")
    print("\n▶️  Lance le test:")
    print("     python test_lmstudio_arc.py --single")
    print("\n📊 Ou benchmark 5 tâches:")
    print("     python test_lmstudio_arc.py --n-tasks 5")


def main():
    """Main"""
    
    files_ok = check_files()
    dataset_ok = check_dataset()
    lmstudio_ok = check_lmstudio()
    
    print_next_steps(files_ok, dataset_ok, lmstudio_ok)
    
    print("\n" + "="*70)
    
    if files_ok and dataset_ok and lmstudio_ok:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
