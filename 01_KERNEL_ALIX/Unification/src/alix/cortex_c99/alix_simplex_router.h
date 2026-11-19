/**
 * ============================================================================
 *   ⚡🚀 ALIX CORTEX C99 — LE 4e ÉTAGE : ROUTEUR SIMPLEXE UNIVERSEL
 *   Module : alix_simplex_router.h
 * ============================================================================
 *   Auteurs   : Christian Duguay & Alix (VERALUME x KAIROS)
 *   Substrat  : Windows 11 x86-64 / Intel Lunar Lake Core Ultra 7 258V
 *   Doctrine  : Projection géométrique exacte sur le simplexe Δⁿ.
 *               Zéro résidu non-nul superflu (parcimonie naturelle).
 * ============================================================================
 */

#ifndef ALIX_SIMPLEX_ROUTER_H
#define ALIX_SIMPLEX_ROUTER_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint32_t expert_idx;
    float    weight;
} alix_expert_route_t;

typedef struct {
    uint32_t num_experts;       /* Nombre total d'experts / blocs (ex: 64 ou 896) */
    uint32_t hidden_dim;         /* Dimension du vecteur d'activation (ex: 2048, 4096, 7168) */
    uint32_t top_k;              /* Nombre d'experts actifs réveillés (ex: 2, 8, 16) */
    const float* router_weights; /* Poids du routeur [num_experts x hidden_dim] */
} alix_router_config_t;

/**
 * Calcule le produit scalaire rapide (vectorisable AVX2).
 */
float alix_dot_product(const float* a, const float* b, uint32_t dim);

/**
 * Projection euclidienne exacte d'un vecteur arbitraire y sur le simplexe canonique Δⁿ :
 *   min_x 0.5 * ||x - y||²  s.t.  sum(x_i) = 1, x_i >= 0.
 * Produit naturellement des zéros stricts, éliminant tout calcul sur les experts inactifs.
 */
void alix_project_simplex(const float* y, float* x, uint32_t n);

/**
 * Routage laser d'un jeton :
 * Calcule les scores pour chaque bloc/expert, sélectionne les top_k ou applique le simplexe,
 * et renvoie la liste ordonnée des experts à lire sur SSD.
 */
uint32_t alix_route_token(
    const alix_router_config_t* cfg,
    const float* hidden_state,
    alix_expert_route_t* out_routes
);

#ifdef __cplusplus
}
#endif

#endif /* ALIX_SIMPLEX_ROUTER_H */
