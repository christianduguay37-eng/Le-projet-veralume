#!/usr/bin/env python3
"""
Téléchargement dataset ARC-AGI officiel
VERALUME/TEMPORIA - Christian Duguay
"""

import os
import json
import urllib.request
from pathlib import Path


def download_arc_dataset(output_dir: str = "arc_data"):
    """
    Télécharge dataset ARC-AGI depuis GitHub officiel
    
    Structure:
    arc_data/
      training.json (400 tâches)
      evaluation.json (400 tâches)
      test.json (100 tâches, solutions privées)
    """
    
    base_url = "https://github.com/fchollet/ARC-AGI/raw/master/data"
    
    datasets = {
        'training': f"{base_url}/training",
        'evaluation': f"{base_url}/evaluation",
        'test': f"{base_url}/test"
    }
    
    # Créer répertoire
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print("="*70)
    print("TÉLÉCHARGEMENT DATASET ARC-AGI")
    print("="*70)
    print(f"Destination: {output_path.absolute()}\n")
    
    for dataset_name, url_prefix in datasets.items():
        print(f"📥 {dataset_name}...")
        
        if dataset_name == 'test':
            # Test set: fichiers individuels
            # On télécharge juste challenges (pas les solutions)
            challenges_url = f"{url_prefix}/challenges.json"
            output_file = output_path / "test_challenges.json"
            
            try:
                urllib.request.urlretrieve(challenges_url, output_file)
                print(f"   ✓ {output_file}")
            except Exception as e:
                print(f"   ✗ Erreur: {e}")
        
        else:
            # Training/Evaluation: télécharger tous les fichiers JSON
            # Format: répertoire avec un fichier .json par tâche
            # On va créer un fichier consolidé
            
            # Liste des tâches (on connait pas à l'avance)
            # Alternative: télécharger archive complète
            consolidated_file = output_path / f"{dataset_name}.json"
            
            # URL vers fichier consolidé (s'il existe)
            consolidated_url = f"{base_url}/{dataset_name}.json"
            
            try:
                urllib.request.urlretrieve(consolidated_url, consolidated_file)
                
                # Valider JSON
                with open(consolidated_file, 'r') as f:
                    data = json.load(f)
                
                n_tasks = len(data) if isinstance(data, dict) else 1
                print(f"   ✓ {consolidated_file} ({n_tasks} tâches)")
                
            except Exception as e:
                print(f"   ✗ Fichier consolidé non disponible")
                print(f"   → Télécharge archive GitHub et extrait manuellement")
                print(f"   git clone https://github.com/fchollet/ARC-AGI.git")
    
    print("\n" + "="*70)
    print("TÉLÉCHARGEMENT TERMINÉ")
    print("="*70)
    print(f"\nDataset disponible dans: {output_path.absolute()}")
    print("\nPour tester:")
    print(f"  python arc_benchmark.py {output_path}/training.json 10")


def verify_dataset(dataset_path: str):
    """Vérifie intégrité dataset"""
    
    print(f"\n📋 Vérification: {dataset_path}")
    
    try:
        with open(dataset_path, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            # Format: {"task_id": {"train": [...], "test": [...]}}
            n_tasks = len(data)
            print(f"   Format: multi-tâches")
            print(f"   Nombre de tâches: {n_tasks}")
            
            # Vérifier premier task
            first_task_id = list(data.keys())[0]
            first_task = data[first_task_id]
            
            print(f"   Exemple (task {first_task_id}):")
            print(f"     Train examples: {len(first_task.get('train', []))}")
            print(f"     Test examples: {len(first_task.get('test', []))}")
            
        else:
            # Format: {"train": [...], "test": [...]}
            print(f"   Format: single task")
            print(f"   Train examples: {len(data.get('train', []))}")
            print(f"   Test examples: {len(data.get('test', []))}")
        
        print("   ✓ Dataset valide")
        return True
        
    except Exception as e:
        print(f"   ✗ Erreur: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "arc_data"
    
    # Télécharger
    download_arc_dataset(output_dir)
    
    # Vérifier
    training_path = os.path.join(output_dir, "training.json")
    if os.path.exists(training_path):
        verify_dataset(training_path)
    
    eval_path = os.path.join(output_dir, "evaluation.json")
    if os.path.exists(eval_path):
        verify_dataset(eval_path)
