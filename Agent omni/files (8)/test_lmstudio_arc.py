"""
Test ARC-AGI avec Omni via LM Studio
Plus simple que llama-cpp-python - pas de compilation
VERALUME/TEMPORIA - Christian Duguay
"""

import sys
from omni_lmstudio_wrapper import OmniLMStudioCore
from omni_arc_agent import OmniAgentARC
from arc_parser import load_arc_tasks, grid_to_ascii, grids_equal, grids_similar


def test_single_task(omni_core, task):
    """Test sur une seule tâche"""
    
    print("\n" + "="*70)
    print(f"TÂCHE: {task.get('id', 'unknown')}")
    print("="*70)
    
    # Init agent
    agent = OmniAgentARC(omni_core=omni_core)
    
    # Résoudre
    predicted, confidence = agent.solve_arc_task(task)
    ground_truth = task['test'][0]['output']
    
    # Résultat
    print("\n" + "─"*70)
    print("RÉSULTAT")
    print("─"*70)
    
    print("\nPrédiction:")
    print(grid_to_ascii(predicted))
    
    print("\nGround Truth:")
    print(grid_to_ascii(ground_truth))
    
    print(f"\nConfiance: {confidence:.2f}")
    
    # Scoring
    if grids_equal(predicted, ground_truth):
        print("\n✅ EXACT MATCH")
        return 1.0, confidence
    elif grids_similar(predicted, ground_truth, threshold=0.8):
        print("\n⚠️  PARTIAL MATCH (≥80% similaire)")
        return 0.5, confidence
    else:
        print("\n❌ MISMATCH")
        return 0.0, confidence


def test_multiple_tasks(omni_core, dataset_path: str, n_tasks: int = 5):
    """Test sur N tâches"""
    
    print("\n" + "="*70)
    print(f"BENCHMARK OMNI LOCAL: {n_tasks} TÂCHES")
    print("="*70)
    
    tasks = load_arc_tasks(dataset_path)[:n_tasks]
    
    results = {
        'exact_match': 0,
        'partial_match': 0,
        'failures': 0,
        'total_confidence': 0.0,
        'scores': []
    }
    
    for idx, task in enumerate(tasks):
        print(f"\n{'─'*70}")
        print(f"Tâche {idx+1}/{n_tasks}")
        
        try:
            score, confidence = test_single_task(omni_core, task)
            
            if score == 1.0:
                results['exact_match'] += 1
            elif score == 0.5:
                results['partial_match'] += 1
            else:
                results['failures'] += 1
            
            results['total_confidence'] += confidence
            results['scores'].append(score)
            
        except Exception as e:
            print(f"\n❌ ERREUR: {e}")
            import traceback
            traceback.print_exc()
            results['failures'] += 1
            results['scores'].append(0.0)
    
    # Résumé
    print("\n" + "="*70)
    print("RÉSUMÉ")
    print("="*70)
    print(f"Tâches testées: {n_tasks}")
    print(f"Exact matches: {results['exact_match']} ({results['exact_match']/n_tasks:.1%})")
    print(f"Partial matches: {results['partial_match']} ({results['partial_match']/n_tasks:.1%})")
    print(f"Failures: {results['failures']} ({results['failures']/n_tasks:.1%})")
    print(f"Accuracy: {results['exact_match']/n_tasks:.2%}")
    print(f"Confiance moyenne: {results['total_confidence']/n_tasks:.2f}")
    
    return results


def main():
    """Script principal"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Test ARC-AGI avec Omni via LM Studio')
    parser.add_argument('--dataset', type=str,
                       default='arc_data/training.json',
                       help='Chemin dataset ARC')
    parser.add_argument('--n-tasks', type=int, default=5,
                       help='Nombre de tâches à tester')
    parser.add_argument('--single', action='store_true',
                       help='Test sur une seule tâche (première)')
    parser.add_argument('--lmstudio-url', type=str,
                       default='http://localhost:1234/v1',
                       help='URL serveur LM Studio')
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("ARC-AGI × OMNI (LM STUDIO)")
    print("="*70)
    print(f"LM Studio: {args.lmstudio_url}")
    print(f"Dataset: {args.dataset}")
    print(f"Tâches: {args.n_tasks if not args.single else 1}")
    
    # Init Omni via LM Studio
    print("\n" + "─"*70)
    print("Connexion LM Studio...")
    print("─"*70)
    
    omni = OmniLMStudioCore(base_url=args.lmstudio_url)
    
    # Charger dataset
    print("\n" + "─"*70)
    print("Chargement dataset...")
    print("─"*70)
    
    try:
        tasks = load_arc_tasks(args.dataset)
        print(f"✓ {len(tasks)} tâches disponibles")
    except FileNotFoundError:
        print(f"❌ Dataset non trouvé: {args.dataset}")
        print("\nTélécharge d'abord:")
        print("  python download_arc_dataset.py")
        return
    
    # Run test
    if args.single:
        # Une seule tâche
        score, confidence = test_single_task(omni, tasks[0])
    else:
        # Multiple tâches
        results = test_multiple_tasks(omni, args.dataset, args.n_tasks)
    
    print("\n" + "="*70)
    print("TERMINÉ")
    print("="*70)


if __name__ == "__main__":
    main()
