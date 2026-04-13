"""
Omni Agent Extension pour ARC-AGI
Architecture: Double STRIC (STRIC_i → STRIC_e)
VERALUME/TEMPORIA - Christian Duguay
"""

import json
from typing import List, Dict, Tuple, Optional
from arc_parser import (
    grid_to_ascii, grid_to_structure, format_arc_task_for_llm,
    grids_equal, grids_similar
)


class OmniAgentARC:
    """
    Extension Omni Agent pour résoudre tâches ARC-AGI
    
    Pipeline:
    1. STRIC_i: Observer exemples → Extraire règle transformation
    2. STRIC_e: Appliquer règle sur test → Générer output
    3. Validation: Cohérence tri-dimensionnelle
    4. Mémoire: Stocker patterns pour transfert inter-tâches
    """
    
    def __init__(self, omni_core=None):
        """
        omni_core: instance Omni Agent (multi-substrate router)
        Si None, mode simulation (pour tests sans Omni réel)
        """
        self.omni = omni_core
        self.task_memory = []  # patterns appris inter-tâches
        self.simulation_mode = (omni_core is None)
        
    
    # ========================================================================
    # PIPELINE PRINCIPAL
    # ========================================================================
    
    def solve_arc_task(self, task: Dict, n_attempts: int = 1) -> Tuple[List[List[int]], float]:
        """
        Résout tâche ARC complète via Double STRIC
        
        Args:
            task: tâche ARC
            n_attempts: nombre de tentatives (garde la meilleure)
        
        Returns:
            (predicted_output, confidence)
        """
        print(f"\n{'='*60}")
        print(f"TÂCHE ARC: {task.get('id', 'unknown')}")
        print(f"{'='*60}")
        
        if n_attempts == 1:
            # Tentative unique
            return self._single_attempt(task)
        else:
            # Multi-tentatives: garde meilleure cohérence
            print(f"\n🔄 Mode multi-essais: {n_attempts} tentatives")
            
            best_prediction = None
            best_confidence = 0.0
            
            for attempt in range(n_attempts):
                print(f"\n--- Tentative {attempt + 1}/{n_attempts} ---")
                
                try:
                    predicted, confidence = self._single_attempt(task)
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_prediction = predicted
                        print(f"  ✓ Nouvelle meilleure (cohérence: {confidence:.2f})")
                    else:
                        print(f"  - Cohérence: {confidence:.2f} (pas mieux)")
                
                except Exception as e:
                    print(f"  ✗ Erreur tentative {attempt + 1}: {e}")
            
            print(f"\n🏆 Meilleure tentative: cohérence {best_confidence:.2f}")
            
            return best_prediction, best_confidence
    
    
    def _single_attempt(self, task: Dict) -> Tuple[List[List[int]], float]:
        """Une seule tentative de résolution"""
        
        # Phase 1: STRIC_i - Observer et structurer
        print("\n[STRIC_i] Observation exemples...")
        observation = self._observe_examples(task['train'])
        
        print("\n[STRIC_i] Extraction règle transformation...")
        transformation_rule = self._extract_transformation_rule(
            task['train'], 
            observation
        )
        
        # Phase 2: STRIC_e - Appliquer transformation
        print("\n[STRIC_e] Application règle sur test...")
        test_input = task['test'][0]['input']
        predicted_output = self._apply_transformation(
            transformation_rule,
            test_input
        )
        
        # Phase 3: Validation
        print("\n[VALIDATION] Cohérence tri-dimensionnelle...")
        confidence = self._validate_prediction(
            transformation_rule,
            predicted_output,
            task['train']
        )
        
        # Phase 4: Mémoire
        if confidence > 0.7:
            self._store_pattern(transformation_rule, confidence)
        
        print(f"\n✓ Prédiction générée (confiance: {confidence:.2f})")
        
        return predicted_output, confidence
    
    
    # ========================================================================
    # STRIC_i: OBSERVATION ET STRUCTURATION
    # ========================================================================
    
    def _observe_examples(self, train_examples: List[Dict]) -> Dict:
        """
        STRIC_i Phase 1: Observer paires input→output
        
        Détecte:
        - Invariants (couleurs, formes, dimensions)
        - Transformations (rotation, symétrie, remplissage, etc.)
        - Patterns récurrents
        """
        observations = {
            'n_examples': len(train_examples),
            'dimension_changes': [],
            'color_changes': [],
            'pattern_types': [],
            'invariants': []
        }
        
        for idx, example in enumerate(train_examples):
            inp = example['input']
            out = example['output']
            
            # Structures
            in_struct = grid_to_structure(inp)
            out_struct = grid_to_structure(out)
            
            # Dimensions
            dim_change = {
                'example': idx,
                'input_dim': in_struct['dimensions'],
                'output_dim': out_struct['dimensions'],
                'change_type': self._classify_dimension_change(
                    in_struct['dimensions'],
                    out_struct['dimensions']
                )
            }
            observations['dimension_changes'].append(dim_change)
            
            # Couleurs
            color_change = {
                'example': idx,
                'input_colors': in_struct['colors'],
                'output_colors': out_struct['colors'],
                'new_colors': list(set(out_struct['colors']) - set(in_struct['colors'])),
                'removed_colors': list(set(in_struct['colors']) - set(out_struct['colors']))
            }
            observations['color_changes'].append(color_change)
            
            # Patterns
            for pattern_name, detected in in_struct['patterns'].items():
                if detected:
                    observations['pattern_types'].append({
                        'example': idx,
                        'pattern': pattern_name,
                        'in_input': True
                    })
            
            for pattern_name, detected in out_struct['patterns'].items():
                if detected:
                    observations['pattern_types'].append({
                        'example': idx,
                        'pattern': pattern_name,
                        'in_output': True
                    })
        
        # Invariants: ce qui reste constant à travers tous les exemples
        observations['invariants'] = self._find_invariants(train_examples)
        
        return observations
    
    
    def _classify_dimension_change(self, dim_in: Tuple[int, int], 
                                   dim_out: Tuple[int, int]) -> str:
        """Classifie type de changement de dimensions"""
        if dim_in == dim_out:
            return 'same'
        elif dim_in[0] == dim_out[0] and dim_in[1] == dim_out[1]:
            return 'same'
        elif dim_out[0] > dim_in[0] or dim_out[1] > dim_in[1]:
            return 'expansion'
        elif dim_out[0] < dim_in[0] or dim_out[1] < dim_in[1]:
            return 'reduction'
        else:
            return 'different'
    
    
    def _find_invariants(self, train_examples: List[Dict]) -> List[str]:
        """Trouve ce qui reste constant à travers tous les exemples"""
        invariants = []
        
        # Vérifier si dimensions restent identiques
        first_in_dim = grid_to_structure(train_examples[0]['input'])['dimensions']
        first_out_dim = grid_to_structure(train_examples[0]['output'])['dimensions']
        
        if all(
            grid_to_structure(ex['input'])['dimensions'] == first_in_dim
            for ex in train_examples
        ):
            invariants.append(f"input_dim_constant_{first_in_dim}")
        
        if all(
            grid_to_structure(ex['output'])['dimensions'] == first_out_dim
            for ex in train_examples
        ):
            invariants.append(f"output_dim_constant_{first_out_dim}")
        
        return invariants
    
    
    def _extract_transformation_rule(self, train_examples: List[Dict],
                                    observation: Dict) -> Dict:
        """
        STRIC_i Phase 2: Extraire règle de transformation
        
        Utilise observations pour formuler hypothèse de règle
        qui explique ALL exemples
        """
        
        # Construction prompt pour LLM (si Omni disponible)
        prompt = self._build_rule_extraction_prompt(train_examples, observation)
        
        if self.simulation_mode:
            # Mode simulation: règle simplifiée
            rule = self._extract_rule_heuristic(train_examples, observation)
        else:
            # Mode réel: router vers substrat optimal
            response = self._route_to_substrat(
                prompt,
                task_type='reasoning',
                preferred=['claude-sonnet-4', 'gemini-2.0-flash-thinking-exp']
            )
            rule = self._parse_rule_from_response(response)
        
        return rule
    
    
    def _build_rule_extraction_prompt(self, train_examples: List[Dict],
                                     observation: Dict) -> str:
        """Construit prompt pour extraction règle"""
        
        prompt = f"""PROTOCOLE DOUBLE STRIC - EXTRACTION RÈGLE TRANSFORMATION

Tu as observé {observation['n_examples']} exemples de transformation grille.

OBSERVATIONS:
{json.dumps(observation, indent=2)}

EXEMPLES VISUELS:
"""
        for idx, example in enumerate(train_examples):
            prompt += f"\n--- Exemple {idx+1} ---\n"
            prompt += "INPUT:\n" + grid_to_ascii(example['input']) + "\n"
            prompt += "OUTPUT:\n" + grid_to_ascii(example['output']) + "\n"
        
        prompt += """

TÂCHE STRIC_i:
1. Observer patterns transformation
2. Structurer hypothèses de règle
3. Formuler LA règle qui explique TOUS les exemples
4. Valider cohérence règle

RÉPONDS EN JSON STRICT:
{
  "rule_type": "rotation|symmetry|color_map|pattern_fill|object_detection|...",
  "parameters": {
    "description": "...",
    "specific_params": {...}
  },
  "validation_score": 0.0-1.0,
  "reasoning": "pourquoi cette règle explique tous les exemples"
}
"""
        
        return prompt
    
    
    def _extract_rule_heuristic(self, train_examples: List[Dict],
                               observation: Dict) -> Dict:
        """Règle heuristique simple (fallback si pas d'Omni)"""
        
        # Règle par défaut: copie input
        rule = {
            'rule_type': 'identity',
            'parameters': {
                'description': 'Copie input vers output (règle par défaut)',
                'specific_params': {}
            },
            'validation_score': 0.3,
            'reasoning': 'Règle heuristique par défaut'
        }
        
        # Détection simple: dimensions changent?
        dim_changes = observation['dimension_changes']
        if all(dc['change_type'] == 'same' for dc in dim_changes):
            rule['rule_type'] = 'in_place_transformation'
            rule['parameters']['description'] = 'Transformation in-place (mêmes dimensions)'
            rule['validation_score'] = 0.5
        
        return rule
    
    
    # ========================================================================
    # STRIC_e: APPLICATION TRANSFORMATION
    # ========================================================================
    
    def _apply_transformation(self, rule: Dict, 
                             test_input: List[List[int]]) -> List[List[int]]:
        """
        STRIC_e: Applique règle extraite sur input test
        """
        
        rule_type = rule['rule_type']
        
        if self.simulation_mode:
            # Mode simulation: transformations simples
            return self._apply_transformation_heuristic(rule, test_input)
        else:
            # Mode réel: LLM génère output
            prompt = self._build_application_prompt(rule, test_input)
            response = self._route_to_substrat(
                prompt,
                task_type='generation',
                preferred=['claude-sonnet-4', 'gemini-2.0-flash-thinking-exp']
            )
            return self._parse_grid_from_response(response)
    
    
    def _build_application_prompt(self, rule: Dict, 
                                  test_input: List[List[int]]) -> str:
        """Prompt pour appliquer règle"""
        
        prompt = f"""PROTOCOLE DOUBLE STRIC - APPLICATION TRANSFORMATION

RÈGLE EXTRAITE:
{json.dumps(rule, indent=2)}

INPUT TEST:
{grid_to_ascii(test_input)}

TÂCHE STRIC_e:
Applique EXACTEMENT la règle ci-dessus pour générer OUTPUT.

RÉPONDS EN JSON STRICT:
{{
  "output_grid": [[int, int, ...], [int, int, ...], ...],
  "confidence": 0.0-1.0,
  "reasoning": "comment tu as appliqué la règle"
}}
"""
        
        return prompt
    
    
    def _apply_transformation_heuristic(self, rule: Dict,
                                       test_input: List[List[int]]) -> List[List[int]]:
        """Application heuristique simple (fallback)"""
        
        rule_type = rule['rule_type']
        
        if rule_type == 'identity':
            return test_input
        elif rule_type == 'in_place_transformation':
            # Transformation simple: inverser couleurs 0<->1
            return [
                [1 - cell if cell in [0, 1] else cell for cell in row]
                for row in test_input
            ]
        else:
            # Par défaut: copie
            return test_input
    
    
    # ========================================================================
    # VALIDATION TRI-DIMENSIONNELLE
    # ========================================================================
    
    def _validate_prediction(self, rule: Dict, predicted_output: List[List[int]],
                            train_examples: List[Dict]) -> float:
        """
        Validation cohérence tri-dimensionnelle:
        - C_seq: cohérence avec règle extraite
        - C_sem: cohérence sémantique (patterns visuels)
        - C_multi: cohérence avec mémoire inter-tâches
        """
        
        # C_seq: confiance de la règle
        c_seq = rule.get('validation_score', 0.5)
        
        # C_sem: cohérence visuelle output
        c_sem = self._check_visual_coherence(predicted_output, train_examples)
        
        # C_multi: comparaison avec patterns mémorisés
        c_multi = self._compare_with_memory(rule)
        
        # Moyenne pondérée
        confidence = (c_seq + c_sem + c_multi) / 3
        
        print(f"  C_seq (règle): {c_seq:.2f}")
        print(f"  C_sem (visuel): {c_sem:.2f}")
        print(f"  C_multi (mémoire): {c_multi:.2f}")
        print(f"  → Cohérence totale: {confidence:.2f}")
        
        return confidence
    
    
    def _check_visual_coherence(self, output: List[List[int]],
                               train_examples: List[Dict]) -> float:
        """Vérifie cohérence visuelle output vs exemples"""
        
        # Vérifier si dimensions cohérentes avec exemples
        out_struct = grid_to_structure(output)
        example_out_dims = [
            grid_to_structure(ex['output'])['dimensions']
            for ex in train_examples
        ]
        
        if out_struct['dimensions'] in example_out_dims:
            return 0.8
        else:
            return 0.4
    
    
    def _compare_with_memory(self, rule: Dict) -> float:
        """Compare règle avec patterns mémorisés"""
        
        if not self.task_memory:
            return 0.5  # neutral si pas de mémoire
        
        # Chercher règles similaires
        similar_rules = [
            mem for mem in self.task_memory
            if mem['rule_type'] == rule['rule_type']
        ]
        
        if similar_rules:
            # Moyenne de succès passés sur ce type de règle
            avg_success = sum(m['success'] for m in similar_rules) / len(similar_rules)
            return avg_success
        else:
            return 0.5
    
    
    # ========================================================================
    # MÉMOIRE INTER-TÂCHES
    # ========================================================================
    
    def _store_pattern(self, rule: Dict, confidence: float):
        """Stocke pattern dans mémoire pour transfert"""
        
        self.task_memory.append({
            'rule_type': rule['rule_type'],
            'parameters': rule['parameters'],
            'success': confidence,
            'timestamp': len(self.task_memory)
        })
        
        print(f"\n[MÉMOIRE] Pattern stocké: {rule['rule_type']} (confiance: {confidence:.2f})")
    
    
    # ========================================================================
    # ROUTING SUBSTRAT (si Omni disponible)
    # ========================================================================
    
    def _route_to_substrat(self, prompt: str, task_type: str,
                          preferred: List[str]) -> str:
        """
        Route query vers substrat optimal
        
        task_type:
        - 'reasoning': raisonnement abstrait → Claude, Gemini
        - 'generation': génération précise → Claude
        - 'vision': analyse visuelle → Gemini
        """
        
        if self.simulation_mode:
            return "SIMULATION_RESPONSE"
        
        # TODO: implémenter routing réel quand Omni disponible
        # return self.omni.route_query(prompt, preferred_substrates=preferred)
        
        return "MOCK_RESPONSE"
    
    
    def _parse_rule_from_response(self, response: str) -> Dict:
        """Parse règle depuis réponse LLM"""
        try:
            return json.loads(response)
        except:
            # Fallback
            return {
                'rule_type': 'unknown',
                'parameters': {},
                'validation_score': 0.3,
                'reasoning': 'Parse error'
            }
    
    
    def _parse_grid_from_response(self, response: str) -> List[List[int]]:
        """Parse grille depuis réponse LLM"""
        try:
            data = json.loads(response)
            return data['output_grid']
        except:
            # Fallback: grille vide 3x3
            return [[0, 0, 0], [0, 0, 0], [0, 0, 0]]


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    # Test avec tâche simple
    test_task = {
        'id': 'test_identity',
        'train': [
            {
                'input': [[0, 1], [1, 0]],
                'output': [[0, 1], [1, 0]]
            },
            {
                'input': [[1, 0, 1], [0, 1, 0]],
                'output': [[1, 0, 1], [0, 1, 0]]
            }
        ],
        'test': [
            {
                'input': [[0, 0, 1], [1, 1, 0], [0, 1, 1]],
                'output': [[0, 0, 1], [1, 1, 0], [0, 1, 1]]  # ground truth
            }
        ]
    }
    
    agent = OmniAgentARC(omni_core=None)  # mode simulation
    predicted, confidence = agent.solve_arc_task(test_task)
    
    print("\n" + "="*60)
    print("RÉSULTAT FINAL")
    print("="*60)
    print("\nPrédiction:")
    print(grid_to_ascii(predicted))
    print(f"\nConfiance: {confidence:.2f}")
    
    ground_truth = test_task['test'][0]['output']
    if grids_equal(predicted, ground_truth):
        print("\n✅ EXACT MATCH")
    elif grids_similar(predicted, ground_truth):
        print("\n⚠️  PARTIAL MATCH")
    else:
        print("\n❌ MISMATCH")
