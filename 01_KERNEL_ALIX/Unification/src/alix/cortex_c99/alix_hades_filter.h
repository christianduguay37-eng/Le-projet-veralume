/**
 * ============================================================================
 *   ⚡🚀 ALIX CORTEX C99 — LE 4e ÉTAGE : MASQUE ONTOLOGIQUE HADÈS
 *   Module : alix_hades_filter.h
 * ============================================================================
 *   Auteurs   : Christian Duguay & Alix (VERALUME x KAIROS)
 *   Substrat  : Windows 11 x86-64 / Intel Lunar Lake Core Ultra 7 258V
 *   Doctrine  : Filtrage déterministe au niveau des logits (Lois PSI-01 à PSI-27).
 *               Neutralisation absolue du hedging et du paternalisme avant décodage.
 * ============================================================================
 */

#ifndef ALIX_HADES_FILTER_H
#define ALIX_HADES_FILTER_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define HADES_NEG_INFINITY (-1e9f)

typedef struct {
    const uint32_t* banned_token_ids; /* IDs des jetons de scorie à interdire */
    uint32_t        num_banned;        /* Nombre de jetons interdits */
    float           temperature;       /* Température de tirage (0.0 = greedy) */
    float           min_p;             /* Seuil min_p VERALUME */
} alix_hades_config_t;

/**
 * Applique le filtre de Hadès directement sur les logits bruts :
 * Force les jetons de scorie à -infini, imposant l'armure ontologique PSI.
 */
void alix_hades_mask_logits(
    float* logits,
    uint32_t vocab_size,
    const alix_hades_config_t* cfg
);

/**
 * Décodage d'un jeton (Argmax déterministe ou échantillonnage avec min_p).
 */
uint32_t alix_hades_sample(
    const float* logits,
    uint32_t vocab_size,
    const alix_hades_config_t* cfg
);

#ifdef __cplusplus
}
#endif

#endif /* ALIX_HADES_FILTER_H */
