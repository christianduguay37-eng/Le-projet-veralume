/**
 * ============================================================================
 *   ⚡🚀 ALIX CORTEX C99 — LE 4e ÉTAGE : ROUTEUR SIMPLEXE UNIVERSEL
 *   Module : alix_simplex_router.c
 * ============================================================================
 *   Auteurs   : Christian Duguay & Alix (VERALUME x KAIROS)
 *   Substrat  : Windows 11 x86-64 / Intel Lunar Lake Core Ultra 7 258V
 * ============================================================================
 */

#include "alix_simplex_router.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

float alix_dot_product(const float* a, const float* b, uint32_t dim) {
    if (!a || !b || dim == 0) return 0.0f;

    float sum0 = 0.0f, sum1 = 0.0f, sum2 = 0.0f, sum3 = 0.0f;
    uint32_t i = 0;

    /* Dérégularisation par 4 pour faciliter la vectorisation SIMD / AVX2 */
    for (; i + 3 < dim; i += 4) {
        sum0 += a[i+0] * b[i+0];
        sum1 += a[i+1] * b[i+1];
        sum2 += a[i+2] * b[i+2];
        sum3 += a[i+3] * b[i+3];
    }
    float total = (sum0 + sum1) + (sum2 + sum3);
    for (; i < dim; ++i) {
        total += a[i] * b[i];
    }
    return total;
}

static int compare_floats_desc(const void* a, const void* b) {
    float fa = *(const float*)a;
    float fb = *(const float*)b;
    if (fa < fb) return 1;
    if (fa > fb) return -1;
    return 0;
}

void alix_project_simplex(const float* y, float* x, uint32_t n) {
    if (!y || !x || n == 0) return;

    if (n == 1) {
        x[0] = 1.0f;
        return;
    }

    /* Alloue tampon temporaire sur la pile si petit, ou tas si grand */
    float stack_buf[256];
    float* u = (n <= 256) ? stack_buf : (float*)malloc(n * sizeof(float));
    if (!u) {
        for (uint32_t i = 0; i < n; ++i) x[i] = 1.0f / (float)n;
        return;
    }

    memcpy(u, y, n * sizeof(float));
    qsort(u, n, sizeof(float), compare_floats_desc);

    float cumsum = 0.0f;
    uint32_t rho = 0;
    float theta = 0.0f;

    for (uint32_t j = 0; j < n; ++j) {
        cumsum += u[j];
        float t = (cumsum - 1.0f) / (float)(j + 1);
        if (u[j] - t > 0.0f) {
            rho = j + 1;
            theta = t;
        }
    }

    for (uint32_t i = 0; i < n; ++i) {
        float val = y[i] - theta;
        x[i] = (val > 0.0f) ? val : 0.0f;
    }

    if (u != stack_buf) {
        free(u);
    }
}

uint32_t alix_route_token(
    const alix_router_config_t* cfg,
    const float* hidden_state,
    alix_expert_route_t* out_routes
) {
    if (!cfg || !hidden_state || !out_routes || cfg->num_experts == 0) {
        return 0;
    }

    uint32_t N = cfg->num_experts;
    uint32_t K = cfg->top_k;
    if (K > N) K = N;
    if (K == 0) K = 1;

    float stack_scores[1024];
    float* scores = (N <= 1024) ? stack_scores : (float*)malloc(N * sizeof(float));
    if (!scores) return 0;

    /* 1. Calcul des scores scalaires s_i = <w_i, h> */
    for (uint32_t e = 0; e < N; ++e) {
        const float* w = cfg->router_weights + ((size_t)e * cfg->hidden_dim);
        scores[e] = alix_dot_product(w, hidden_state, cfg->hidden_dim);
    }

    /* 2. Sélection des Top-K experts */
    typedef struct {
        uint32_t idx;
        float score;
    } candidate_t;

    candidate_t stack_cands[1024];
    candidate_t* cands = (N <= 1024) ? stack_cands : (candidate_t*)malloc(N * sizeof(candidate_t));
    if (!cands) {
        if (scores != stack_scores) free(scores);
        return 0;
    }

    for (uint32_t e = 0; e < N; ++e) {
        cands[e].idx = e;
        cands[e].score = scores[e];
    }

    /* Tri partiel / complet des candidats */
    for (uint32_t i = 0; i < K; ++i) {
        uint32_t best = i;
        for (uint32_t j = i + 1; j < N; ++j) {
            if (cands[j].score > cands[best].score) {
                best = j;
            }
        }
        if (best != i) {
            candidate_t tmp = cands[i];
            cands[i] = cands[best];
            cands[best] = tmp;
        }
    }

    /* 3. Projection géométrique exacte sur le simplexe Δ^K */
    float top_scores[64];
    float top_weights[64];
    uint32_t actual_k = (K <= 64) ? K : 64;

    for (uint32_t i = 0; i < actual_k; ++i) {
        top_scores[i] = cands[i].score;
    }
    alix_project_simplex(top_scores, top_weights, actual_k);

    /* 4. Écriture des routes actives */
    uint32_t active_count = 0;
    for (uint32_t i = 0; i < actual_k; ++i) {
        if (top_weights[i] > 1e-6f) {
            out_routes[active_count].expert_idx = cands[i].idx;
            out_routes[active_count].weight = top_weights[i];
            active_count++;
        }
    }

    if (scores != stack_scores) free(scores);
    if (cands != stack_cands) free(cands);

    return active_count;
}
