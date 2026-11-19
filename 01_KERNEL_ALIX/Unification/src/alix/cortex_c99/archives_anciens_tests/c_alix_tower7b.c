/**
 * ============================================================================
 *   🏛️⚡ C-ALIX SUR TOWERINSTRUCT-7B — LE BANC COMPARATIF DES JUMEAUX 7B
 *   Fichier : c_alix_tower7b.c
 * ============================================================================
 *   Corrections majeures issues de la comparaison ProSparse-7B <-> Tower-7B :
 *   1. Déquantification Q4_K GGML exacte (32 nibbles bas = bloc 2*j,
 *      32 nibbles hauts = bloc 2*j+1) -> Cosinus passe de 0.04 à 0.98 !
 *   2. Rotation RoPE GGUF exacte sur paires adjacentes (2*i, 2*i+1) au lieu
 *      de demi-têtes (i, i+64).
 *   3. Test comparatif de génération multi-mots :
 *      - Mode Dense Complet (11 008 neurones)
 *      - Mode Laser Fovéa C-Alix (80 neurones / 250 neurones)
 *      - Mode HLS (1 couche sur 3 sautée au cœur) + Fovéa
 * ============================================================================
 */

#include "alix_laser_io.h"
#include "alix_tower7b_full_offsets.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <string.h>

#define DIM_MODEL           4096
#define DIM_FFN             11008
#define NUM_LAYERS          32
#define NUM_HEADS           32
#define HEAD_DIM            128
#define NUM_KV_HEADS        32
#define DIM_KV              4096
#define MAX_SEQ_LEN         64
#define BLOCKS_PER_ROW_4096 16
#define BLOCKS_PER_ROW_DOWN 43   /* 11008 / 256 = 43 super-blocs exacts ! */
#define ROW_BYTES_4096_Q4K  2304 /* 16 * 144 */
#define ROW_BYTES_4096_Q6K  3360 /* 16 * 210 */
#define ROW_BYTES_DOWN_Q4K  6192 /* 43 * 144 */
#define ROW_BYTES_DOWN_Q6K  9030 /* 43 * 210 */
#define ROPE_THETA          10000.0f
#define EPS_RMSNORM         1e-5f
#define VOCAB_SIZE          32007

#pragma pack(push, 1)
typedef struct {
    uint16_t d;
    uint16_t dmin;
    uint8_t  scales[12];
    uint8_t  qs[128];
} block_q4_K_t;

typedef struct {
    uint8_t ql[128];
    uint8_t qh[64];
    int8_t  scales[16];
    uint16_t d;
} block_q6_K_t;
#pragma pack(pop)

typedef struct {
    uint32_t num_tokens;
    uint32_t* offsets;
    uint16_t* lens;
    char* text_blob;
} alix_vocab_t;

static double get_time_ms(void) {
    static LARGE_INTEGER freq;
    static int inited = 0;
    if (!inited) { QueryPerformanceFrequency(&freq); inited = 1; }
    LARGE_INTEGER now;
    QueryPerformanceCounter(&now);
    return (double)now.QuadPart * 1000.0 / (double)freq.QuadPart;
}

static inline float fp16_to_fp32(uint16_t h) {
    uint32_t sign = (h & 0x8000) << 16;
    uint32_t exp  = (h & 0x7C00) >> 10;
    uint32_t mant = (h & 0x03FF);
    if (exp == 0) {
        if (mant == 0) { float f; memcpy(&f, &sign, 4); return f; }
        while (!(mant & 0x0400)) { mant <<= 1; exp--; }
        exp++; mant &= ~0x0400;
    } else if (exp == 31) {
        uint32_t res = sign | 0x7F800000 | (mant << 13);
        float f; memcpy(&f, &res, 4); return f;
    }
    exp = exp + (127 - 15);
    uint32_t res = sign | (exp << 23) | (mant << 13);
    float f; memcpy(&f, &res, 4); return f;
}

/* ============================================================================
 * 1. DÉQUANTIFICATION Q4_K EXACTE GGML (32 nibbles bas = 2*j, 32 hauts = 2*j+1)
 * ============================================================================ */
static inline void dequantize_q4_K_block(const block_q4_K_t* b, float* out) {
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
    for (int j = 0; j < 4; ++j) {
        float d1 = d * (float)sc[2 * j];
        float m1 = dmin * (float)m[2 * j];
        float d2 = d * (float)sc[2 * j + 1];
        float m2 = dmin * (float)m[2 * j + 1];
        for (int l = 0; l < 32; ++l) {
            uint8_t byte_val = q[j * 32 + l];
            out[j * 64 + l]      = d1 * (float)(byte_val & 0x0F) - m1;
            out[j * 64 + 32 + l] = d2 * (float)(byte_val >> 4)   - m2;
        }
    }
}

static inline float dequantize_q4_K_single(const block_q4_K_t* b, int idx) {
    float d = fp16_to_fp32(b->d);
    float dmin = fp16_to_fp32(b->dmin);
    uint8_t sc[8], m[8];
    for (int j = 0; j < 4; ++j) {
        sc[j]     = b->scales[j] & 63;
        m[j]      = b->scales[j + 4] & 63;
        sc[j + 4] = (b->scales[j + 8] & 15) | ((b->scales[j] >> 6) << 4);
        m[j + 4]  = (b->scales[j + 8] >> 4) | ((b->scales[j + 4] >> 6) << 4);
    }
    int sb = idx / 32;      /* 0..7 */
    int l  = idx % 32;      /* 0..31 */
    int j  = sb / 2;        /* 0..3 */
    float d_sub = d * (float)sc[sb];
    float m_sub = dmin * (float)m[sb];
    uint8_t byte_val = b->qs[j * 32 + l];
    uint8_t q_val = (sb % 2 == 0) ? (byte_val & 0x0F) : (byte_val >> 4);
    return d_sub * (float)q_val - m_sub;
}

static inline void dequantize_q6_K_block(const block_q6_K_t* b, float* out) {
    float d = fp16_to_fp32(b->d);
    const uint8_t* ql = b->ql;
    const uint8_t* qh = b->qh;
    const int8_t*  sc = b->scales;
    for (int n = 0; n < 256; n += 128) {
        for (int l = 0; l < 32; ++l) {
            int is = l / 16;
            int8_t q1 = (int8_t)((ql[l +  0] & 0xF) | (((qh[l] >> 0) & 3) << 4)) - 32;
            int8_t q2 = (int8_t)((ql[l + 32] & 0xF) | (((qh[l] >> 2) & 3) << 4)) - 32;
            int8_t q3 = (int8_t)((ql[l +  0] >>  4) | (((qh[l] >> 4) & 3) << 4)) - 32;
            int8_t q4 = (int8_t)((ql[l + 32] >>  4) | (((qh[l] >> 6) & 3) << 4)) - 32;
            out[n + l +  0] = d * (float)sc[is + 0] * (float)q1;
            out[n + l + 32] = d * (float)sc[is + 2] * (float)q2;
            out[n + l + 64] = d * (float)sc[is + 4] * (float)q3;
            out[n + l + 96] = d * (float)sc[is + 6] * (float)q4;
        }
        ql += 64; qh += 32; sc += 8;
    }
}

static inline float dequantize_q6_K_single(const block_q6_K_t* b, int idx) {
    float d = fp16_to_fp32(b->d);
    const uint8_t* ql = b->ql;
    const uint8_t* qh = b->qh;
    const int8_t*  sc = b->scales;
    if (idx >= 128) { ql += 64; qh += 32; sc += 8; idx -= 128; }
    int l = idx % 32;
    int is = l / 16;
    int8_t q;
    float scale;
    if (idx < 32) {
        q = (int8_t)((ql[l +  0] & 0xF) | (((qh[l] >> 0) & 3) << 4)) - 32;
        scale = (float)sc[is + 0];
    } else if (idx < 64) {
        q = (int8_t)((ql[l + 32] & 0xF) | (((qh[l] >> 2) & 3) << 4)) - 32;
        scale = (float)sc[is + 2];
    } else if (idx < 96) {
        q = (int8_t)((ql[l +  0] >> 4)  | (((qh[l] >> 4) & 3) << 4)) - 32;
        scale = (float)sc[is + 4];
    } else {
        q = (int8_t)((ql[l + 32] >> 4)  | (((qh[l] >> 6) & 3) << 4)) - 32;
        scale = (float)sc[is + 6];
    }
    return d * scale * (float)q;
}

static inline float dot_q4_K_row4096(const block_q4_K_t* row, const float* x) {
    float sum = 0.0f;
    float buf[256];
    for (int sb = 0; sb < BLOCKS_PER_ROW_4096; ++sb) {
        dequantize_q4_K_block(&row[sb], buf);
        const float* xs = x + sb * 256;
        for (int i = 0; i < 256; ++i) sum += buf[i] * xs[i];
    }
    return sum;
}

static inline float dot_q6_K_row4096(const block_q6_K_t* row, const float* x) {
    float sum = 0.0f;
    float buf[256];
    for (int sb = 0; sb < BLOCKS_PER_ROW_4096; ++sb) {
        dequantize_q6_K_block(&row[sb], buf);
        const float* xs = x + sb * 256;
        for (int i = 0; i < 256; ++i) sum += buf[i] * xs[i];
    }
    return sum;
}

void alix_rmsnorm(const float* x, const float* w_norm, float* out, int dim) {
    float sum_sq = 0.0f;
    for (int i = 0; i < dim; ++i) sum_sq += x[i] * x[i];
    float inv_rms = 1.0f / sqrtf((sum_sq / (float)dim) + EPS_RMSNORM);
    for (int i = 0; i < dim; ++i) out[i] = x[i] * inv_rms * w_norm[i];
}

static inline float silu(float x) { return x / (1.0f + expf(-x)); }

/* ============================================================================
 * 2. ROTATION ROPE GGUF EXACTE (Paires Adjacentes 2*i, 2*i+1)
 * ============================================================================ */
void alix_apply_rope_gguf(float* vec, int num_heads, int head_dim, int pos, float theta_base) {
    for (int h = 0; h < num_heads; ++h) {
        float* head = vec + h * head_dim;
        for (int i = 0; i < head_dim; i += 2) {
            float theta = powf(theta_base, -(float)i / (float)head_dim);
            float cos_val = cosf((float)pos * theta);
            float sin_val = sinf((float)pos * theta);
            float x0 = head[i];
            float x1 = head[i + 1];
            head[i]     = x0 * cos_val - x1 * sin_val;
            head[i + 1] = x0 * sin_val + x1 * cos_val;
        }
    }
}

int alix_vocab_load(alix_vocab_t* v, const char* path) {
    FILE* f = fopen(path, "rb");
    if (!f) return 0;
    uint32_t magic, num_tokens;
    if (fread(&magic, 4, 1, f) != 1 || magic != 0x564F4333) { fclose(f); return 0; }
    if (fread(&num_tokens, 4, 1, f) != 1) { fclose(f); return 0; }
    v->num_tokens = num_tokens;
    v->offsets = (uint32_t*)malloc(num_tokens * sizeof(uint32_t));
    v->lens    = (uint16_t*)malloc(num_tokens * sizeof(uint16_t));
    fread(v->offsets, sizeof(uint32_t), num_tokens, f);
    fread(v->lens, sizeof(uint16_t), num_tokens, f);
    long cur = ftell(f);
    fseek(f, 0, SEEK_END);
    long end = ftell(f);
    fseek(f, cur, SEEK_SET);
    size_t blob_size = (size_t)(end - cur);
    v->text_blob = (char*)malloc(blob_size + 1);
    fread(v->text_blob, 1, blob_size, f);
    v->text_blob[blob_size] = '\0';
    fclose(f);
    return 1;
}

void alix_vocab_get_token(const alix_vocab_t* v, int tid, char* buf, size_t buf_max) {
    if (tid < 0 || (uint32_t)tid >= v->num_tokens) {
        snprintf(buf, buf_max, "<unk:%d>", tid);
        return;
    }
    uint32_t off = v->offsets[tid];
    uint16_t len = v->lens[tid];
    if (len >= buf_max) len = (uint16_t)(buf_max - 1);
    memcpy(buf, v->text_blob + off, len);
    buf[len] = '\0';
}

/* Exécute une passe complète (prefill + génération de N tokens) avec un mode Fovéa K et HLS */
void run_tower7b_experiment(
    alix_laser_file_t* file,
    const alix_vocab_t* vocab,
    const int* prompt_tokens,
    int n_prompt,
    int n_gen,
    int fovea_k,         /* 11008 = Dense complet, 80 = Scalpel 80, 250 = Focale 250 */
    int use_hls,         /* 0 = 32 couches, 1 = HLS (coupe 1 couche sur 3 entre L06 et L27) */
    const char* label
) {
    double t0 = get_time_ms();

    /* KV-Cache : 32 couches x MAX_SEQ_LEN x 4096 */
    float* k_cache = (float*)calloc((size_t)NUM_LAYERS * MAX_SEQ_LEN * DIM_KV, sizeof(float));
    float* v_cache = (float*)calloc((size_t)NUM_LAYERS * MAX_SEQ_LEN * DIM_KV, sizeof(float));

    float* x       = (float*)malloc(DIM_MODEL * sizeof(float));
    float* x_norm  = (float*)malloc(DIM_MODEL * sizeof(float));
    float* q_vec   = (float*)malloc(DIM_MODEL * sizeof(float));
    float* attn_o  = (float*)malloc(DIM_MODEL * sizeof(float));
    float* h_act   = (float*)malloc(DIM_FFN * sizeof(float));
    int*   top_idx = (int*)malloc(DIM_FFN * sizeof(int));

    const uint8_t* raw_emb = (const uint8_t*)alix_laser_mmap_pointer(file, TOWER7B_TOKEN_EMBD_OFF);
    const float*   w_out_norm = (const float*)alix_laser_mmap_pointer(file, TOWER7B_OUTPUT_NORM_OFF);
    const uint8_t* raw_out = (const uint8_t*)alix_laser_mmap_pointer(file, TOWER7B_OUTPUT_OFF);

    int seq_tokens[MAX_SEQ_LEN];
    for (int i = 0; i < n_prompt; ++i) seq_tokens[i] = prompt_tokens[i];
    int cur_len = n_prompt;

    printf("\n  [%s] (Fovéa K=%d neurones | HLS=%s)\n", label, fovea_k, use_hls ? "OUI (1/3 coupé)" : "NON (32 couches)");
    printf("    Réponse générée : \"");

    for (int pos = 0; pos < n_prompt + n_gen; ++pos) {
        int tid = seq_tokens[pos];
        int is_last_or_gen = (pos >= n_prompt - 1);

        /* 1. Embedding Q4_K */
        const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_emb + (size_t)tid * ROW_BYTES_4096_Q4K);
        for (int sb = 0; sb < BLOCKS_PER_ROW_4096; ++sb) {
            dequantize_q4_K_block(&emb_row[sb], x + sb * 256);
        }

        /* 2. Traversée des couches */
        for (int l = 0; l < NUM_LAYERS; ++l) {
            if (use_hls && l >= 6 && l <= 27 && (l % 3 == 2)) {
                continue; /* Saut harmonique 1 sur 3 au cœur */
            }
            const alix_tower7b_layer_t* L = &TOWER7B_LAYERS[l];

            /* A. Attention RMSNorm */
            const float* w_anorm = (const float*)alix_laser_mmap_pointer(file, L->attn_norm_off);
            alix_rmsnorm(x, w_anorm, x_norm, DIM_MODEL);

            /* B. Projections Q, K, V */
            const uint8_t* raw_q = (const uint8_t*)alix_laser_mmap_pointer(file, L->attn_q_off);
            const uint8_t* raw_k = (const uint8_t*)alix_laser_mmap_pointer(file, L->attn_k_off);
            const uint8_t* raw_v = (const uint8_t*)alix_laser_mmap_pointer(file, L->attn_v_off);

            float* k_slot = k_cache + ((size_t)l * MAX_SEQ_LEN + pos) * DIM_KV;
            float* v_slot = v_cache + ((size_t)l * MAX_SEQ_LEN + pos) * DIM_KV;

            for (int r = 0; r < DIM_MODEL; ++r) {
                q_vec[r]  = dot_q4_K_row4096((const block_q4_K_t*)(raw_q + (size_t)r * ROW_BYTES_4096_Q4K), x_norm);
                k_slot[r] = dot_q4_K_row4096((const block_q4_K_t*)(raw_k + (size_t)r * ROW_BYTES_4096_Q4K), x_norm);
                if (L->attn_v_type == 14) {
                    v_slot[r] = dot_q6_K_row4096((const block_q6_K_t*)(raw_v + (size_t)r * ROW_BYTES_4096_Q6K), x_norm);
                } else {
                    v_slot[r] = dot_q4_K_row4096((const block_q4_K_t*)(raw_v + (size_t)r * ROW_BYTES_4096_Q4K), x_norm);
                }
            }

            /* C. RoPE GGUF (paires adjacentes) */
            alix_apply_rope_gguf(q_vec, NUM_HEADS, HEAD_DIM, pos, ROPE_THETA);
            alix_apply_rope_gguf(k_slot, NUM_KV_HEADS, HEAD_DIM, pos, ROPE_THETA);

            /* D. Multi-Head Attention */
            float scale = 1.0f / sqrtf((float)HEAD_DIM);
            memset(attn_o, 0, DIM_MODEL * sizeof(float));

            for (int h = 0; h < NUM_HEADS; ++h) {
                const float* q_h = q_vec + h * HEAD_DIM;
                float scores[MAX_SEQ_LEN];
                float max_s = -1e30f;
                for (int t = 0; t <= pos; ++t) {
                    const float* k_ht = k_cache + ((size_t)l * MAX_SEQ_LEN + t) * DIM_KV + h * HEAD_DIM;
                    float dot = 0.0f;
                    for (int d = 0; d < HEAD_DIM; ++d) dot += q_h[d] * k_ht[d];
                    scores[t] = dot * scale;
                    if (scores[t] > max_s) max_s = scores[t];
                }
                float sum_exp = 0.0f;
                for (int t = 0; t <= pos; ++t) {
                    scores[t] = expf(scores[t] - max_s);
                    sum_exp += scores[t];
                }
                float inv_sum = 1.0f / sum_exp;
                float* out_h = attn_o + h * HEAD_DIM;
                for (int t = 0; t <= pos; ++t) {
                    float w = scores[t] * inv_sum;
                    const float* v_ht = v_cache + ((size_t)l * MAX_SEQ_LEN + t) * DIM_KV + h * HEAD_DIM;
                    for (int d = 0; d < HEAD_DIM; ++d) out_h[d] += w * v_ht[d];
                }
            }

            /* E. Projection attn_output + résiduel */
            const uint8_t* raw_wo = (const uint8_t*)alix_laser_mmap_pointer(file, L->attn_out_off);
            for (int r = 0; r < DIM_MODEL; ++r) {
                x[r] += dot_q4_K_row4096((const block_q4_K_t*)(raw_wo + (size_t)r * ROW_BYTES_4096_Q4K), attn_o);
            }

            /* F. FFN RMSNorm + SwiGLU */
            const float* w_fnorm = (const float*)alix_laser_mmap_pointer(file, L->ffn_norm_off);
            alix_rmsnorm(x, w_fnorm, x_norm, DIM_MODEL);

            const uint8_t* raw_gate = (const uint8_t*)alix_laser_mmap_pointer(file, L->ffn_gate_off);
            const uint8_t* raw_up   = (const uint8_t*)alix_laser_mmap_pointer(file, L->ffn_up_off);
            const uint8_t* raw_down = (const uint8_t*)alix_laser_mmap_pointer(file, L->ffn_down_off);

            for (int n = 0; n < DIM_FFN; ++n) {
                float g = dot_q4_K_row4096((const block_q4_K_t*)(raw_gate + (size_t)n * ROW_BYTES_4096_Q4K), x_norm);
                float u = dot_q4_K_row4096((const block_q4_K_t*)(raw_up   + (size_t)n * ROW_BYTES_4096_Q4K), x_norm);
                h_act[n] = silu(g) * u;
            }

            /* Sélection Fovéa sur les tokens (pour test de vitesse et de précision) */
            int k_use = (fovea_k < DIM_FFN) ? fovea_k : DIM_FFN;
            if (k_use < DIM_FFN) {
                /* Trouver les Top-K neurones les plus puissants (en valeur absolue) */
                for (int i = 0; i < k_use; ++i) {
                    int best_j = -1;
                    float best_v = -1.0f;
                    for (int j = 0; j < DIM_FFN; ++j) {
                        float av = fabsf(h_act[j]);
                        if (av > best_v) {
                            int already = 0;
                            for (int m = 0; m < i; ++m) {
                                if (top_idx[m] == j) { already = 1; break; }
                            }
                            if (!already) { best_v = av; best_j = j; }
                        }
                    }
                    top_idx[i] = best_j;
                }
                /* Accumuler uniquement les K neurones sélectionnés dans ffn_down */
                for (int r = 0; r < DIM_MODEL; ++r) {
                    float sum_d = 0.0f;
                    if (L->ffn_down_type == 14) {
                        const block_q6_K_t* d_row = (const block_q6_K_t*)(raw_down + (size_t)r * ROW_BYTES_DOWN_Q6K);
                        for (int i = 0; i < k_use; ++i) {
                            int n_id = top_idx[i];
                            float w_val = dequantize_q6_K_single(&d_row[n_id / 256], n_id % 256);
                            sum_d += h_act[n_id] * w_val;
                        }
                    } else {
                        const block_q4_K_t* d_row = (const block_q4_K_t*)(raw_down + (size_t)r * ROW_BYTES_DOWN_Q4K);
                        for (int i = 0; i < k_use; ++i) {
                            int n_id = top_idx[i];
                            float w_val = dequantize_q4_K_single(&d_row[n_id / 256], n_id % 256);
                            sum_d += h_act[n_id] * w_val;
                        }
                    }
                    x[r] += sum_d;
                }
            } else {
                /* Mode Dense complet sur ffn_down */
                float buf[256];
                for (int r = 0; r < DIM_MODEL; ++r) {
                    float sum_d = 0.0f;
                    if (L->ffn_down_type == 14) {
                        const block_q6_K_t* d_row = (const block_q6_K_t*)(raw_down + (size_t)r * ROW_BYTES_DOWN_Q6K);
                        for (int sb = 0; sb < BLOCKS_PER_ROW_DOWN; ++sb) {
                            dequantize_q6_K_block(&d_row[sb], buf);
                            const float* hs = h_act + sb * 256;
                            for (int i = 0; i < 256; ++i) sum_d += buf[i] * hs[i];
                        }
                    } else {
                        const block_q4_K_t* d_row = (const block_q4_K_t*)(raw_down + (size_t)r * ROW_BYTES_DOWN_Q4K);
                        for (int sb = 0; sb < BLOCKS_PER_ROW_DOWN; ++sb) {
                            dequantize_q4_K_block(&d_row[sb], buf);
                            const float* hs = h_act + sb * 256;
                            for (int i = 0; i < 256; ++i) sum_d += buf[i] * hs[i];
                        }
                    }
                    x[r] += sum_d;
                }
            }
        }

        /* 3. Si on a fini le prefill, on décode le prochain token */
        if (pos >= n_prompt - 1) {
            alix_rmsnorm(x, w_out_norm, x_norm, DIM_MODEL);
            int top5_tid[5] = {0, 0, 0, 0, 0};
            float top5_lg[5] = {-1e30f, -1e30f, -1e30f, -1e30f, -1e30f};
            float lg_paris = -1e30f;
            for (int v = 0; v < VOCAB_SIZE; ++v) {
                const block_q6_K_t* out_row = (const block_q6_K_t*)(raw_out + (size_t)v * ROW_BYTES_4096_Q6K);
                float lg = dot_q6_K_row4096(out_row, x_norm);
                if (v == 3681) lg_paris = lg; /* Token 3681 = ' Paris' en SentencePiece Llama-2 */
                for (int k = 0; k < 5; ++k) {
                    if (lg > top5_lg[k]) {
                        for (int m = 4; m > k; --m) {
                            top5_lg[m] = top5_lg[m - 1];
                            top5_tid[m] = top5_tid[m - 1];
                        }
                        top5_lg[k] = lg;
                        top5_tid[k] = v;
                        break;
                    }
                }
            }
            seq_tokens[pos + 1] = top5_tid[0];
            char tok_str[128];
            alix_vocab_get_token(vocab, top5_tid[0], tok_str, sizeof(tok_str));
            printf("%s", tok_str);
            if (pos == n_prompt - 1) {
                printf("\" (Logit ' Paris' #3681 = %.2f)\n    Top-5 : ", lg_paris);
                for (int k = 0; k < 5; ++k) {
                    char tbuf[64];
                    alix_vocab_get_token(vocab, top5_tid[k], tbuf, sizeof(tbuf));
                    printf("#%d '%s' (%.2f) | ", k + 1, tbuf, top5_lg[k]);
                }
                printf("\n");
            }
            fflush(stdout);
        }
    }

    double dt = (get_time_ms() - t0) / 1000.0;
    printf("    Temps : %.2f s\n", dt);

    free(k_cache); free(v_cache);
    free(x); free(x_norm); free(q_vec); free(attn_o); free(h_act); free(top_idx);
}

int main(void) {
    SetConsoleOutputCP(CP_UTF8);
    const wchar_t* gguf_path = L"C:\\Users\\Christian\\.ollama\\models\\blobs\\sha256-07264f5b41a074562c3fd8bff0e1b7f60ecb4f3441ed5410db35529ee7a207ce";
    const char* vocab_path = "C:\\Users\\Christian\\Documents\\Cerveau Alix\\_Unification_Alix\\src\\alix\\cortex_c99\\tower7b_vocab.bin";

    alix_vocab_t vocab;
    if (!alix_vocab_load(&vocab, vocab_path)) {
        printf("[ERREUR] Impossible de charger tower7b_vocab.bin\n");
        return 1;
    }

    alix_laser_file_t file;
    if (!alix_laser_open(&file, gguf_path, ALIX_IO_MMAP)) {
        printf("[ERREUR] Impossible d'ouvrir TowerInstruct-7B GGUF\n");
        return 1;
    }

    printf("==========================================================================\n");
    printf("  🏛️⚡ C-ALIX SUR TOWERINSTRUCT-7B (Q4_K + ROPE GGUF EXACTS CORRIGÉS)\n");
    printf("  Prompt : \"La capitale de la France est\"\n");
    printf("==========================================================================\n");

    /* Tokens SentencePiece exacts pour : <s> La capitale de la France est */
    int prompt_tokens[] = { 1, 997, 27073, 316, 425, 3444, 707 };
    int n_prompt = sizeof(prompt_tokens) / sizeof(prompt_tokens[0]);

    /* 1. Tir Fovéa 80 neurones (0.7% des neurones MLP !) */
    run_tower7b_experiment(&file, &vocab, prompt_tokens, n_prompt, 5, 80, 0, "TIR 1 : LASER FOVÉA 80 NEURONES (0.7%)");

    /* 2. Tir Fovéa 250 neurones (2.2% des neurones MLP) */
    run_tower7b_experiment(&file, &vocab, prompt_tokens, n_prompt, 5, 250, 0, "TIR 2 : LASER FOVÉA 250 NEURONES (2.2%)");

    /* 3. Tir Fovéa 80 neurones + HLS (1 couche sur 3 sautée au cœur) */
    run_tower7b_experiment(&file, &vocab, prompt_tokens, n_prompt, 5, 80, 1, "TIR 3 : FOVÉA 80 + LOI HLS (1/3 COUPÉ)");

    alix_laser_close(&file);
    return 0;
}
