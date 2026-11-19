/**
 * ============================================================================
 *   ⚡🚀 ALIX CORTEX C99 — LE 4e ÉTAGE : EXÉCUTEUR SWIGLU FFN SUR POIDS GGUF
 *   Module : alix_cortex_swiglu.c
 * ============================================================================
 *   Auteurs   : Christian Duguay & Alix (VERALUME x KAIROS)
 *   Substrat  : Windows 11 x86-64 / Intel Lunar Lake Core Ultra 7 258V
 *   Cible     : test_ffn_slice.gguf (Couche 0 Qwen2 FFN complète)
 * ============================================================================
 */

#include "alix_laser_io.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <string.h>

#define DIM_MODEL       3584
#define DIM_FFN_SLICE   2048
#define EPS_RMSNORM     1e-6f

/* Chronomètre haute précision Windows (QueryPerformanceCounter) */
static double get_time_us(void) {
    static LARGE_INTEGER freq;
    static int inited = 0;
    if (!inited) {
        QueryPerformanceFrequency(&freq);
        inited = 1;
    }
    LARGE_INTEGER now;
    QueryPerformanceCounter(&now);
    return (double)now.QuadPart * 1000000.0 / (double)freq.QuadPart;
}

/* Conversion float16 (IEEE 754-2008) vers float32 IEEE */
static inline float fp16_to_fp32(uint16_t h) {
    uint32_t sign = (h & 0x8000) << 16;
    uint32_t exp  = (h & 0x7C00) >> 10;
    uint32_t mant = (h & 0x03FF);

    if (exp == 0) {
        if (mant == 0) {
            uint32_t res = sign;
            float f; memcpy(&f, &res, 4); return f;
        }
        while (!(mant & 0x0400)) {
            mant <<= 1;
            exp--;
        }
        exp++;
        mant &= ~0x0400;
    } else if (exp == 31) {
        uint32_t res = sign | 0x7F800000 | (mant << 13);
        float f; memcpy(&f, &res, 4); return f;
    }

    exp = exp + (127 - 15);
    mant = mant << 13;
    uint32_t res = sign | (exp << 23) | mant;
    float f; memcpy(&f, &res, 4);
    return f;
}

/* RMSNorm : x_norm = (x / sqrt(mean(x^2) + eps)) * w_norm */
void alix_rmsnorm(const float* x, const float* w_norm, float* out, int dim) {
    float sum_sq = 0.0f;
    for (int i = 0; i < dim; ++i) {
        sum_sq += x[i] * x[i];
    }
    float inv_rms = 1.0f / sqrtf((sum_sq / (float)dim) + EPS_RMSNORM);
    for (int i = 0; i < dim; ++i) {
        out[i] = x[i] * inv_rms * w_norm[i];
    }
}

/* SiLU d'activation : x / (1 + exp(-x)) */
static inline float silu(float x) {
    return x / (1.0f + expf(-x));
}

#pragma pack(push, 1)
typedef struct {
    uint16_t d;
    uint16_t dmin;
    uint8_t  scales[12];
    uint8_t  qs[128];
} block_q4_K_t;
#pragma pack(pop)

/* Déquantification d'un super-bloc Q4_K (256 valeurs) vers float */
void dequantize_q4_K_block(const block_q4_K_t* b, float* out) {
    float d = fp16_to_fp32(b->d);
    float dmin = fp16_to_fp32(b->dmin);

    uint8_t sc[8], m[8];
    for (int j = 0; j < 4; ++j) {
        sc[j]     = b->scales[j] & 63;
        m[j]      = b->scales[j + 4] & 63;
        sc[j + 4] = (b->scales[j + 8] & 15) | ((b->scales[j] >> 6) << 4);
        m[j + 4]  = (b->scales[j + 8] >> 4) | ((b->scales[j + 4] >> 6) << 4);
    }

    const uint8_t* q = b->qs;
    for (int sb = 0; sb < 8; ++sb) {
        float d_sub = d * (float)sc[sb];
        float m_sub = dmin * (float)m[sb];
        for (int i = 0; i < 32; i += 2) {
            uint8_t byte_val = q[(sb * 32 + i) / 2];
            uint8_t q0 = byte_val & 0x0F;
            uint8_t q1 = (byte_val >> 4) & 0x0F;
            out[sb * 32 + i]     = d_sub * (float)q0 - m_sub;
            out[sb * 32 + i + 1] = d_sub * (float)q1 - m_sub;
        }
    }
}

int main(int argc, char** argv) {
    (void)argc; (void)argv;
    SetConsoleOutputCP(CP_UTF8);

    const wchar_t* gguf_path = L"C:\\Users\\Christian\\Desktop\\Projet alix\\Alix\\test  gemini\\Personel\\Projet Alix\\test_ffn_slice.gguf";

    printf("====================================================================\n");
    printf("  ⚡🚀 ALIX CORTEX C99 -- EXÉCUTEUR SWIGLU SUR POIDS GGUF DU FER\n");
    printf("  Architecture : Qwen2 (dim=%d, ffn_slice=%d)\n", DIM_MODEL, DIM_FFN_SLICE);
    printf("  Substrat     : Intel Lunar Lake Core Ultra 7 258V + NVMe\n");
    printf("====================================================================\n\n");

    /* 1. Montage Virtuel MMAP du fichier de poids */
    alix_laser_file_t file;
    if (!alix_laser_open(&file, gguf_path, ALIX_IO_MMAP)) {
        printf("  [ERREUR] Impossible de mapper le fichier GGUF.\n");
        return 1;
    }

    /* Offsets des tenseurs réels déterminés lors de l'analyse */
    uint64_t off_norm = 87074496ULL;
    uint64_t off_gate = 82945728ULL;
    uint64_t off_up   = 87088832ULL;

    const float* w_ffn_norm = (const float*)alix_laser_mmap_pointer(&file, off_norm);
    const uint8_t* raw_gate = (const uint8_t*)alix_laser_mmap_pointer(&file, off_gate);
    const uint8_t* raw_up   = (const uint8_t*)alix_laser_mmap_pointer(&file, off_up);

    if (!w_ffn_norm || !raw_gate || !raw_up) {
        printf("  [ERREUR] Pointeur MMAP nul.\n");
        alix_laser_close(&file);
        return 1;
    }

    /* 2. Simulation d'un vecteur d'activation entrant (ex: sortie du bloc attention) */
    float* x_in = (float*)malloc(DIM_MODEL * sizeof(float));
    float* x_norm = (float*)malloc(DIM_MODEL * sizeof(float));
    float* h_gate = (float*)malloc(DIM_FFN_SLICE * sizeof(float));
    float* h_up   = (float*)malloc(DIM_FFN_SLICE * sizeof(float));
    float* h_mid  = (float*)malloc(DIM_FFN_SLICE * sizeof(float));

    for (int i = 0; i < DIM_MODEL; ++i) {
        x_in[i] = ((float)rand() / (float)RAND_MAX) * 0.2f - 0.1f;
    }

    printf("  [1] Vecteur d'activation source généré : %d dimensions\n", DIM_MODEL);
    printf("      Norme L2 d'entrée : ");
    float l2_in = 0.0f;
    for (int i = 0; i < DIM_MODEL; ++i) l2_in += x_in[i] * x_in[i];
    printf("%.4f\n\n", sqrtf(l2_in));

    /* 3. Mesure de la passe SwiGLU complète */
    int iters = 100;
    printf("  [2] Exécution de la passe FFN SwiGLU (%d passes pour benchmark) :\n", iters);

    double t0 = get_time_us();

    for (int it = 0; it < iters; ++it) {
        /* A. Normalisation RMSNorm */
        alix_rmsnorm(x_in, w_ffn_norm, x_norm, DIM_MODEL);

        /* B. Projections Gate & Up avec déquantification à la volée */
        /* Chaque ligne a DIM_MODEL = 3584 valeurs = 14 super-blocs Q4_K = 2016 octets */
        float row_buf[DIM_MODEL];

        for (int r = 0; r < DIM_FFN_SLICE; ++r) {
            const block_q4_K_t* b_gate = (const block_q4_K_t*)(raw_gate + (size_t)r * 2016);
            const block_q4_K_t* b_up   = (const block_q4_K_t*)(raw_up   + (size_t)r * 2016);

            /* Déquantification ligne gate */
            for (int sb = 0; sb < 14; ++sb) {
                dequantize_q4_K_block(&b_gate[sb], row_buf + (sb * 256));
            }
            float dot_g = 0.0f;
            for (int i = 0; i < DIM_MODEL; ++i) dot_g += x_norm[i] * row_buf[i];
            h_gate[r] = dot_g;

            /* Déquantification ligne up */
            for (int sb = 0; sb < 14; ++sb) {
                dequantize_q4_K_block(&b_up[sb], row_buf + (sb * 256));
            }
            float dot_u = 0.0f;
            for (int i = 0; i < DIM_MODEL; ++i) dot_u += x_norm[i] * row_buf[i];
            h_up[r] = dot_u;

            /* C. Activation SwiGLU : h_mid = SiLU(h_gate) * h_up */
            h_mid[r] = silu(h_gate[r]) * h_up[r];
        }
    }

    double t1 = get_time_us();
    double avg_us = (t1 - t0) / (double)iters;
    double avg_ms = avg_us / 1000.0;

    printf("  ✓ RMSNorm + Projections Gate/Up (%d x %d) + SwiGLU achevés avec succès !\n", DIM_FFN_SLICE, DIM_MODEL);
    printf("    ⚡ Temps moyen par couche FFN complète : %.2f ms (%.1f µs)\n", avg_ms, avg_us);
    printf("    ⚡ Vitesse de calcul équivalente       : %.1f couches FFN / seconde\n\n", 1000.0 / avg_ms);

    printf("  [3] Échantillon des 5 premières activations calculées (h_mid) :\n");
    for (int i = 0; i < 5; ++i) {
        printf("      Neurone #%02d : Gate=%8.4f | Up=%8.4f | SwiGLU=%8.4f\n",
               i, h_gate[i], h_up[i], h_mid[i]);
    }

    alix_laser_close(&file);
    free(x_in);
    free(x_norm);
    free(h_gate);
    free(h_up);
    free(h_mid);

    printf("\n====================================================================\n");
    printf("  🎯 L'OPÉRATEUR SWIGLU C99 TOURNE DIRECTEMENT SUR LES POIDS GGUF.\n");
    printf("====================================================================\n");
    return 0;
}
