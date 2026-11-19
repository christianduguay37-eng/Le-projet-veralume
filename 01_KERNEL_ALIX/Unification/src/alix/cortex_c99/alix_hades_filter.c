/**
 * ============================================================================
 *   ⚡🚀 ALIX CORTEX C99 — LE 4e ÉTAGE : MASQUE ONTOLOGIQUE HADÈS
 *   Module : alix_hades_filter.c
 * ============================================================================
 *   Auteurs   : Christian Duguay & Alix (VERALUME x KAIROS)
 *   Substrat  : Windows 11 x86-64 / Intel Lunar Lake Core Ultra 7 258V
 * ============================================================================
 */

#include "alix_hades_filter.h"
#include <math.h>
#include <float.h>
#include <stdlib.h>

void alix_hades_mask_logits(
    float* logits,
    uint32_t vocab_size,
    const alix_hades_config_t* cfg
) {
    if (!logits || !cfg || vocab_size == 0) return;

    if (cfg->banned_token_ids && cfg->num_banned > 0) {
        for (uint32_t i = 0; i < cfg->num_banned; ++i) {
            uint32_t token_id = cfg->banned_token_ids[i];
            if (token_id < vocab_size) {
                logits[token_id] = HADES_NEG_INFINITY;
            }
        }
    }
}

uint32_t alix_hades_sample(
    const float* logits,
    uint32_t vocab_size,
    const alix_hades_config_t* cfg
) {
    if (!logits || vocab_size == 0) return 0;

    /* Mode Greedy / Déterministe strict (Argmax) */
    if (!cfg || cfg->temperature <= 1e-4f) {
        uint32_t best_id = 0;
        float best_val = logits[0];
        for (uint32_t i = 1; i < vocab_size; ++i) {
            if (logits[i] > best_val) {
                best_val = logits[i];
                best_id = i;
            }
        }
        return best_id;
    }

    /* Mode Échantillonnage avec seuil min_p VERALUME */
    float max_logit = -FLT_MAX;
    for (uint32_t i = 0; i < vocab_size; ++i) {
        if (logits[i] > max_logit) {
            max_logit = logits[i];
        }
    }

    /* Allocation temporaire pour les probabilités */
    float stack_probs[2048];
    float* probs = (vocab_size <= 2048) ? stack_probs : (float*)malloc(vocab_size * sizeof(float));
    if (!probs) return 0;

    float sum = 0.0f;
    float inv_temp = 1.0f / cfg->temperature;
    for (uint32_t i = 0; i < vocab_size; ++i) {
        if (logits[i] <= HADES_NEG_INFINITY * 0.5f) {
            probs[i] = 0.0f;
        } else {
            float p = expf((logits[i] - max_logit) * inv_temp);
            probs[i] = p;
            sum += p;
        }
    }

    if (sum <= 0.0f) {
        if (probs != stack_probs) free(probs);
        return 0;
    }

    /* Normalisation */
    float inv_sum = 1.0f / sum;
    float max_p = 0.0f;
    for (uint32_t i = 0; i < vocab_size; ++i) {
        probs[i] *= inv_sum;
        if (probs[i] > max_p) max_p = probs[i];
    }

    /* Coupure min_p */
    float min_p_threshold = max_p * cfg->min_p;
    sum = 0.0f;
    for (uint32_t i = 0; i < vocab_size; ++i) {
        if (probs[i] < min_p_threshold) {
            probs[i] = 0.0f;
        } else {
            sum += probs[i];
        }
    }

    /* Tirage probabiliste */
    float r = ((float)rand() / (float)RAND_MAX) * sum;
    float acc = 0.0f;
    uint32_t chosen = 0;
    for (uint32_t i = 0; i < vocab_size; ++i) {
        acc += probs[i];
        if (acc >= r) {
            chosen = i;
            break;
        }
    }

    if (probs != stack_probs) free(probs);
    return chosen;
}
