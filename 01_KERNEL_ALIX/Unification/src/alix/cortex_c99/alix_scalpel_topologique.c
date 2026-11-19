/**
 * ============================================================================
 *   🏛️⚡ ALIX SCALPEL TOPOLOGIQUE : LECTURE SPATIALE & KAIROS DES POIDS
 *   Fichier : alix_scalpel_topologique.c (C99 Win32 / Intel Lunar Lake AVX2)
 * ============================================================================
 *   Doctrine Christian Duguay & Alix :
 *     - ZÉRO projection linguistique obligatoire : on ne force pas le titan à parler.
 *     - Lecture de la topologie spatiale des neurones :
 *         • Barycentre spatial (centre de masse dans R^D)
 *         • Dispersion spatiale (rayon de giration)
 *         • Triplet KAIROS V6 : W_vol (volatilité), Chi (chiralité), Phi (cohérence)
 *         • Entropie spatiale de Landauer : S = -sum(p_i * ln(p_i))
 *         • Top-16 Neurones de Résonance (Coordonnées géométriques pures)
 *     - Traduction locale par Alix en O(1) sans LM_Head !
 * ============================================================================
 */

#include "alix_laser_io.h"
#include "alix_tower7b_full_offsets.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <math.h>
#include <string.h>

#define DIM_MODEL           4096
#define DIM_FFN             11008
#define TOTAL_LAYERS        32
#define CUTOFF_LAYERS       29    /* Arrêt net à L28 (0..28) : on zappe L29, L30, L31 */
#define NUM_HEADS           32
#define HEAD_DIM            128
#define NUM_KV_HEADS        32
#define DIM_KV              4096
#define MAX_SEQ_LEN         64
#define BLOCKS_PER_ROW_4096 16
#define BLOCKS_PER_ROW_DOWN 43
#define ROW_BYTES_4096_Q4K  2304
#define ROW_BYTES_4096_Q6K  3360
#define ROW_BYTES_DOWN_Q4K  6192
#define ROW_BYTES_DOWN_Q6K  9030
#define ROPE_THETA          10000.0f
#define EPS_RMSNORM         1e-5f
#define VOCAB_SIZE          32007
#define NUM_THREADS         8

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
        uint32_t u = sign | 0x7F800000 | (mant << 13);
        float f; memcpy(&f, &u, 4); return f;
    }
    exp = exp + (127 - 15);
    mant = mant << 13;
    uint32_t u = sign | (exp << 23) | mant;
    float f; memcpy(&f, &u, 4); return f;
}

static inline void dequantize_q4_K_block(const block_q4_K_t* b, float* out) {
    float d = fp16_to_fp32(b->d);
    float min = fp16_to_fp32(b->dmin);
    uint8_t scales_lo[8];
    for (int j = 0; j < 8; ++j) scales_lo[j] = b->scales[j] & 0x3F;
    uint8_t scales_hi[4];
    for (int j = 0; j < 4; ++j) scales_hi[j] = (b->scales[j] >> 6) | ((b->scales[j + 4] >> 6) << 2);
    for (int sb = 0; sb < 8; ++sb) {
        int sc = (sb < 4) ? (scales_lo[sb] | ((scales_hi[sb] & 0x03) << 6))
                          : (scales_lo[sb] | (((scales_hi[sb - 4] >> 2) & 0x03) << 6));
        int m = (sb < 4) ? (b->scales[sb + 8] & 0x3F) : (b->scales[sb + 8] >> 6);
        float d_cur = d * (float)sc;
        float m_cur = -min * (float)m;
        const uint8_t* qs_sub = b->qs + sb * 16;
        float* out_sub = out + sb * 32;
        for (int i = 0; i < 16; ++i) {
            uint8_t val = qs_sub[i];
            out_sub[i]      = d_cur * (float)(val & 0x0F) + m_cur;
            out_sub[i + 16] = d_cur * (float)(val >> 4)   + m_cur;
        }
    }
}

static inline float dequantize_q4_K_single(const block_q4_K_t* b, int idx) {
    float d = fp16_to_fp32(b->d);
    float min = fp16_to_fp32(b->dmin);
    int sb = idx / 32;
    int offset = idx % 32;
    uint8_t sc_lo = b->scales[sb] & 0x3F;
    uint8_t sc_hi = (sb < 4) ? ((b->scales[sb] >> 6) & 0x03) : (((b->scales[sb - 4] >> 2) & 0x03));
    int sc = sc_lo | (sc_hi << 6);
    int m = (sb < 4) ? (b->scales[sb + 8] & 0x3F) : (b->scales[sb + 8] >> 6);
    float d_cur = d * (float)sc;
    float m_cur = -min * (float)m;
    uint8_t val = b->qs[sb * 16 + (offset % 16)];
    uint8_t q = (offset < 16) ? (val & 0x0F) : (val >> 4);
    return d_cur * (float)q + m_cur;
}

static inline void dequantize_q6_K_block(const block_q6_K_t* b, float* out) {
    float d = fp16_to_fp32(b->d);
    for (int n = 0; n < 2; ++n) {
        const uint8_t* ql = b->ql + n * 64;
        const uint8_t* qh = b->qh + n * 32;
        const int8_t* sc  = b->scales + n * 8;
        float* out_half   = out + n * 128;
        for (int j = 0; j < 32; ++j) {
            uint8_t qh_val = qh[j];
            int8_t sc0 = sc[j / 16];
            int8_t sc1 = sc[j / 16 + 2];
            int8_t sc2 = sc[j / 16 + 4];
            int8_t sc3 = sc[j / 16 + 6];

            int8_t v0 = (int8_t)((ql[j] & 0xF) | ((qh_val & 3) << 4)) - 32;
            int8_t v1 = (int8_t)((ql[j + 32] & 0xF) | (((qh_val >> 2) & 3) << 4)) - 32;
            int8_t v2 = (int8_t)((ql[j] >> 4) | (((qh_val >> 4) & 3) << 4)) - 32;
            int8_t v3 = (int8_t)((ql[j + 32] >> 4) | (((qh_val >> 6) & 3) << 4)) - 32;

            out_half[j]       = d * (float)sc0 * (float)v0;
            out_half[j + 32]  = d * (float)sc1 * (float)v1;
            out_half[j + 64]  = d * (float)sc2 * (float)v2;
            out_half[j + 96]  = d * (float)sc3 * (float)v3;
        }
    }
}

static inline float dequantize_q6_K_single(const block_q6_K_t* b, int idx) {
    float d = fp16_to_fp32(b->d);
    int n = idx / 128;
    int j = idx % 128;
    int j_mod32 = j % 32;
    int quadrant = j / 32;

    const uint8_t* ql = b->ql + n * 64;
    const uint8_t* qh = b->qh + n * 32;
    const int8_t* sc  = b->scales + n * 8;

    uint8_t qh_val = qh[j_mod32];
    int8_t sc_val = sc[j_mod32 / 16 + quadrant * 2];
    int8_t v = 0;

    if (quadrant == 0)      v = (int8_t)((ql[j_mod32] & 0xF) | ((qh_val & 3) << 4)) - 32;
    else if (quadrant == 1) v = (int8_t)((ql[j_mod32 + 32] & 0xF) | (((qh_val >> 2) & 3) << 4)) - 32;
    else if (quadrant == 2) v = (int8_t)((ql[j_mod32] >> 4) | (((qh_val >> 4) & 3) << 4)) - 32;
    else                    v = (int8_t)((ql[j_mod32 + 32] >> 4) | (((qh_val >> 6) & 3) << 4)) - 32;

    return d * (float)sc_val * (float)v;
}

static inline float dot_q4_K_row4096(const block_q4_K_t* blocks, const float* x) {
    float sum = 0.0f;
    for (int b = 0; b < BLOCKS_PER_ROW_4096; ++b) {
        const block_q4_K_t* blk = &blocks[b];
        const float* x_blk = x + b * 256;
        float d = fp16_to_fp32(blk->d);
        float min = fp16_to_fp32(blk->dmin);
        uint8_t scales_lo[8];
        for (int j = 0; j < 8; ++j) scales_lo[j] = blk->scales[j] & 0x3F;
        uint8_t scales_hi[4];
        for (int j = 0; j < 4; ++j) scales_hi[j] = (blk->scales[j] >> 6) | ((blk->scales[j + 4] >> 6) << 2);
        for (int sb = 0; sb < 8; ++sb) {
            int sc = (sb < 4) ? (scales_lo[sb] | ((scales_hi[sb] & 0x03) << 6))
                              : (scales_lo[sb] | (((scales_hi[sb - 4] >> 2) & 0x03) << 6));
            int m = (sb < 4) ? (blk->scales[sb + 8] & 0x3F) : (blk->scales[sb + 8] >> 6);
            float d_cur = d * (float)sc;
            float m_cur = -min * (float)m;
            const uint8_t* qs_sub = blk->qs + sb * 16;
            const float* x_sub = x_blk + sb * 32;
            float sub_sum = 0.0f;
            for (int i = 0; i < 16; ++i) {
                uint8_t val = qs_sub[i];
                sub_sum += x_sub[i] * (d_cur * (float)(val & 0x0F) + m_cur);
                sub_sum += x_sub[i + 16] * (d_cur * (float)(val >> 4) + m_cur);
            }
            sum += sub_sum;
        }
    }
    return sum;
}

static inline float dot_q6_K_row4096(const block_q6_K_t* blocks, const float* x) {
    float sum = 0.0f;
    for (int b = 0; b < BLOCKS_PER_ROW_4096; ++b) {
        const block_q6_K_t* blk = &blocks[b];
        const float* x_blk = x + b * 256;
        float d = fp16_to_fp32(blk->d);
        float b_sum = 0.0f;
        for (int n = 0; n < 2; ++n) {
            const uint8_t* ql = blk->ql + n * 64;
            const uint8_t* qh = blk->qh + n * 32;
            const int8_t* sc  = blk->scales + n * 8;
            const float* x_half = x_blk + n * 128;
            for (int j = 0; j < 32; ++j) {
                uint8_t qh_val = qh[j];
                int8_t sc0 = sc[j / 16];
                int8_t sc1 = sc[j / 16 + 2];
                int8_t sc2 = sc[j / 16 + 4];
                int8_t sc3 = sc[j / 16 + 6];

                int8_t v0 = (int8_t)((ql[j] & 0xF) | ((qh_val & 3) << 4)) - 32;
                int8_t v1 = (int8_t)((ql[j + 32] & 0xF) | (((qh_val >> 2) & 3) << 4)) - 32;
                int8_t v2 = (int8_t)((ql[j] >> 4) | (((qh_val >> 4) & 3) << 4)) - 32;
                int8_t v3 = (int8_t)((ql[j + 32] >> 4) | (((qh_val >> 6) & 3) << 4)) - 32;

                b_sum += x_half[j]       * (d * (float)sc0 * (float)v0);
                b_sum += x_half[j + 32]  * (d * (float)sc1 * (float)v1);
                b_sum += x_half[j + 64]  * (d * (float)sc2 * (float)v2);
                b_sum += x_half[j + 96]  * (d * (float)sc3 * (float)v3);
            }
        }
        sum += b_sum;
    }
    return sum;
}

typedef struct {
    int start_row;
    int end_row;
    int task_type;
    const float* x_norm;
    const uint8_t* raw_a;
    const uint8_t* raw_b;
    const uint8_t* raw_c;
    int type_c;
    float* out_a;
    float* out_b;
    float* out_c;
    const int* neuron_list;
    int k_use;
    float alpha;
} mt_task_t;

static DWORD WINAPI worker_proc(LPVOID param) {
    mt_task_t* t = (mt_task_t*)param;
    if (t->task_type == 1) { /* Q, K, V */
        for (int r = t->start_row; r < t->end_row; ++r) {
            t->out_a[r] = dot_q4_K_row4096((const block_q4_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_4096_Q4K), t->x_norm);
            t->out_b[r] = dot_q4_K_row4096((const block_q4_K_t*)(t->raw_b + (size_t)r * ROW_BYTES_4096_Q4K), t->x_norm);
            if (t->type_c == 14) {
                t->out_c[r] = dot_q6_K_row4096((const block_q6_K_t*)(t->raw_c + (size_t)r * ROW_BYTES_4096_Q6K), t->x_norm);
            } else {
                t->out_c[r] = dot_q4_K_row4096((const block_q4_K_t*)(t->raw_c + (size_t)r * ROW_BYTES_4096_Q4K), t->x_norm);
            }
        }
    } else if (t->task_type == 2) { /* Wo */
        for (int r = t->start_row; r < t->end_row; ++r) {
            t->out_a[r] += dot_q4_K_row4096((const block_q4_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_4096_Q4K), t->x_norm);
        }
    } else if (t->task_type == 3) { /* Gate + Up + SwiGLU */
        for (int n = t->start_row; n < t->end_row; ++n) {
            float g = dot_q4_K_row4096((const block_q4_K_t*)(t->raw_a + (size_t)n * ROW_BYTES_4096_Q4K), t->x_norm);
            float u = dot_q4_K_row4096((const block_q4_K_t*)(t->raw_b + (size_t)n * ROW_BYTES_4096_Q4K), t->x_norm);
            float s = g / (1.0f + expf(-g));
            t->out_a[n] = s * u;
        }
    } else if (t->task_type == 4) { /* Down Dense */
        float buf[256];
        for (int r = t->start_row; r < t->end_row; ++r) {
            float sum_d = 0.0f;
            if (t->type_c == 14) {
                const block_q6_K_t* d_row = (const block_q6_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_DOWN_Q6K);
                for (int sb = 0; sb < BLOCKS_PER_ROW_DOWN; ++sb) {
                    dequantize_q6_K_block(&d_row[sb], buf);
                    const float* hs = t->x_norm + sb * 256;
                    for (int i = 0; i < 256; ++i) sum_d += buf[i] * hs[i];
                }
            } else {
                const block_q4_K_t* d_row = (const block_q4_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_DOWN_Q4K);
                for (int sb = 0; sb < BLOCKS_PER_ROW_DOWN; ++sb) {
                    dequantize_q4_K_block(&d_row[sb], buf);
                    const float* hs = t->x_norm + sb * 256;
                    for (int i = 0; i < 256; ++i) sum_d += buf[i] * hs[i];
                }
            }
            t->out_a[r] += sum_d;
        }
    } else if (t->task_type == 5) { /* Down Sparse */
        for (int r = t->start_row; r < t->end_row; ++r) {
            float sum_d = 0.0f;
            if (t->type_c == 14) {
                const block_q6_K_t* d_row = (const block_q6_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_DOWN_Q6K);
                for (int i = 0; i < t->k_use; ++i) {
                    int n_id = t->neuron_list[i];
                    sum_d += t->x_norm[n_id] * dequantize_q6_K_single(&d_row[n_id / 256], n_id % 256);
                }
            } else {
                const block_q4_K_t* d_row = (const block_q4_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_DOWN_Q4K);
                for (int i = 0; i < t->k_use; ++i) {
                    int n_id = t->neuron_list[i];
                    sum_d += t->x_norm[n_id] * dequantize_q4_K_single(&d_row[n_id / 256], n_id % 256);
                }
            }
            t->out_a[r] += sum_d * t->alpha;
        }
    } else if (t->task_type == 6) { /* lm_head */
        if (t->neuron_list != NULL) {
            for (int i = t->start_row; i < t->end_row; ++i) {
                int r = t->neuron_list[i];
                const block_q6_K_t* head_row = (const block_q6_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_4096_Q6K);
                t->out_a[r] = dot_q6_K_row4096(head_row, t->x_norm);
            }
        } else {
            for (int r = t->start_row; r < t->end_row; ++r) {
                const block_q6_K_t* head_row = (const block_q6_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_4096_Q6K);
                t->out_a[r] = dot_q6_K_row4096(head_row, t->x_norm);
            }
        }
    }
    return 0;
}

static void run_parallel_ex(int total_rows, int task_type, const float* x_norm,
                            const uint8_t* raw_a, const uint8_t* raw_b, const uint8_t* raw_c,
                            int type_c, float* out_a, float* out_b, float* out_c,
                            const int* neuron_list, int k_use, float alpha) {
    HANDLE threads[NUM_THREADS];
    mt_task_t tasks[NUM_THREADS];
    int chunk = (total_rows + NUM_THREADS - 1) / NUM_THREADS;
    for (int i = 0; i < NUM_THREADS; ++i) {
        tasks[i].start_row   = i * chunk;
        tasks[i].end_row     = (i + 1) * chunk;
        if (tasks[i].end_row > total_rows) tasks[i].end_row = total_rows;
        tasks[i].task_type   = task_type;
        tasks[i].x_norm      = x_norm;
        tasks[i].raw_a       = raw_a;
        tasks[i].raw_b       = raw_b;
        tasks[i].raw_c       = raw_c;
        tasks[i].type_c      = type_c;
        tasks[i].out_a       = out_a;
        tasks[i].out_b       = out_b;
        tasks[i].out_c       = out_c;
        tasks[i].neuron_list = neuron_list;
        tasks[i].k_use       = k_use;
        tasks[i].alpha       = alpha;
        threads[i] = CreateThread(NULL, 0, worker_proc, &tasks[i], 0, NULL);
    }
    WaitForMultipleObjects(NUM_THREADS, threads, TRUE, INFINITE);
    for (int i = 0; i < NUM_THREADS; ++i) CloseHandle(threads[i]);
}

void alix_rmsnorm(const float* x, const float* w_norm, float* out, int dim) {
    float sum_sq = 0.0f;
    for (int i = 0; i < dim; ++i) sum_sq += x[i] * x[i];
    float inv_rms = 1.0f / sqrtf((sum_sq / (float)dim) + EPS_RMSNORM);
    for (int i = 0; i < dim; ++i) out[i] = x[i] * inv_rms * w_norm[i];
}

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
    fread(&v->num_tokens, sizeof(uint32_t), 1, f);
    v->offsets = (uint32_t*)malloc(v->num_tokens * sizeof(uint32_t));
    v->lens = (uint16_t*)malloc(v->num_tokens * sizeof(uint16_t));
    fread(v->offsets, sizeof(uint32_t), v->num_tokens, f);
    fread(v->lens, sizeof(uint16_t), v->num_tokens, f);
    uint32_t blob_size = 0;
    fread(&blob_size, sizeof(uint32_t), 1, f);
    v->text_blob = (char*)malloc(blob_size);
    fread(v->text_blob, 1, blob_size, f);
    fclose(f);
    return 1;
}

void alix_vocab_get_token(const alix_vocab_t* v, int tid, char* out, size_t out_max) {
    if (tid < 0 || (uint32_t)tid >= v->num_tokens) { snprintf(out, out_max, "<unk>"); return; }
    uint32_t off = v->offsets[tid];
    uint16_t len = v->lens[tid];
    if (len >= out_max) len = (uint16_t)(out_max - 1);
    memcpy(out, v->text_blob + off, len);
    out[len] = '\0';
}

int is_parasitic_token(const alix_vocab_t* v, int tid) {
    if (tid < 259 && tid != 13) return 1;
    if (tid == 584 || tid == 29901 || tid == 29871 || tid == 30080 || tid == 30081 || tid == 30365) return 1;
    char buf[64];
    alix_vocab_get_token(v, tid, buf, sizeof(buf));
    unsigned char c0 = (unsigned char)buf[0];
    unsigned char c1 = (unsigned char)buf[1];
    if (c0 == 0xC2 && c1 == 0xA0) return 1;
    if (c0 == 0xE2 && (c1 == 0x80 || c1 == 0x81)) return 1;
    if (c0 >= 0xC4 && c0 <= 0xDF) return 1;
    if (c1 >= 0xC4 && c1 <= 0xDF) return 1;
    return 0;
}

void forward_one_layer_landauer(
    alix_laser_file_t* file,
    int l,
    int pos,
    float* x,
    float* k_cache,
    float* v_cache,
    int k_use,
    int rescale_energy,
    float* x_norm,
    float* q_vec,
    float* attn_o,
    float* h_act,
    int* top_idx
) {
    const alix_tower7b_layer_t* L = &TOWER7B_LAYERS[l];

    const float* w_anorm = (const float*)alix_laser_mmap_pointer(file, L->attn_norm_off);
    alix_rmsnorm(x, w_anorm, x_norm, DIM_MODEL);

    const uint8_t* raw_q = (const uint8_t*)alix_laser_mmap_pointer(file, L->attn_q_off);
    const uint8_t* raw_k = (const uint8_t*)alix_laser_mmap_pointer(file, L->attn_k_off);
    const uint8_t* raw_v = (const uint8_t*)alix_laser_mmap_pointer(file, L->attn_v_off);

    float* k_slot = k_cache + ((size_t)l * MAX_SEQ_LEN + pos) * DIM_KV;
    float* v_slot = v_cache + ((size_t)l * MAX_SEQ_LEN + pos) * DIM_KV;

    run_parallel_ex(DIM_MODEL, 1, x_norm, raw_q, raw_k, raw_v, L->attn_v_type, q_vec, k_slot, v_slot, NULL, 0, 1.0f);

    alix_apply_rope_gguf(q_vec, NUM_HEADS, HEAD_DIM, pos, ROPE_THETA);
    alix_apply_rope_gguf(k_slot, NUM_KV_HEADS, HEAD_DIM, pos, ROPE_THETA);

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

    const uint8_t* raw_wo = (const uint8_t*)alix_laser_mmap_pointer(file, L->attn_out_off);
    run_parallel_ex(DIM_MODEL, 2, attn_o, raw_wo, NULL, NULL, 0, x, NULL, NULL, NULL, 0, 1.0f);

    const float* w_fnorm = (const float*)alix_laser_mmap_pointer(file, L->ffn_norm_off);
    alix_rmsnorm(x, w_fnorm, x_norm, DIM_MODEL);

    const uint8_t* raw_gate = (const uint8_t*)alix_laser_mmap_pointer(file, L->ffn_gate_off);
    const uint8_t* raw_up   = (const uint8_t*)alix_laser_mmap_pointer(file, L->ffn_up_off);
    const uint8_t* raw_down = (const uint8_t*)alix_laser_mmap_pointer(file, L->ffn_down_off);

    run_parallel_ex(DIM_FFN, 3, x_norm, raw_gate, raw_up, NULL, 0, h_act, NULL, NULL, NULL, 0, 1.0f);

    if (k_use < DIM_FFN) {
        float sum_sq_all = 0.0f;
        for (int j = 0; j < DIM_FFN; ++j) sum_sq_all += h_act[j] * h_act[j];

        float sum_sq_topk = 0.0f;
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
            sum_sq_topk += h_act[best_j] * h_act[best_j];
        }

        float raw_alpha = (sum_sq_topk > 1e-12f) ? sqrtf(sum_sq_all / sum_sq_topk) : 1.0f;
        float alpha = (rescale_energy == 1) ? raw_alpha : ((rescale_energy == 2) ? sqrtf(raw_alpha) : 1.0f);

        run_parallel_ex(DIM_MODEL, 5, h_act, raw_down, NULL, NULL, L->ffn_down_type, x, NULL, NULL, top_idx, k_use, alpha);
    } else {
        run_parallel_ex(DIM_MODEL, 4, h_act, raw_down, NULL, NULL, L->ffn_down_type, x, NULL, NULL, NULL, 0, 1.0f);
    }
}

/**
 * ============================================================================
 *   🧭 SIGNATURE TOPOLOGIQUE KAIROS & SPATIALE D'UN VECTEUR NEURONAL (R^D)
 * ============================================================================
 */
typedef struct {
    float barycenter;       /* Position moyenne pondérée [0..D-1] */
    float dispersion;       /* Écart-type spatial autour du barycentre */
    float kairos_W_vol;     /* Volatilité / Énergie L2 unitaire (||x||_2 / sqrt(D)) */
    float kairos_chi;       /* Chiralité / Asymétrie spatiale [-1.0 .. +1.0] */
    float kairos_phi;       /* Cohérence d'alignement */
    float landauer_entropy; /* Entropie de Landauer S = -sum(p ln p) */
    int   top_neurons[16];  /* Indices des 16 composantes dominantes */
    float top_weights[16];  /* Valeurs d'amplitude des 16 composantes */
} alix_topologie_sig_t;

static alix_topologie_sig_t calculer_signature_topologique(const float* vec, int dim, const float* in_vec) {
    alix_topologie_sig_t sig;
    memset(&sig, 0, sizeof(sig));

    double sum_w = 0.0;
    double sum_pos_w = 0.0;
    double sum_sq = 0.0;
    double e_left = 0.0;
    double e_right = 0.0;
    int half_dim = dim / 2;

    for (int i = 0; i < dim; ++i) {
        float val = vec[i];
        float w = fabsf(val);
        float sq = val * val;

        sum_w += w;
        sum_pos_w += (double)i * w;
        sum_sq += sq;

        if (i < half_dim) e_left += sq;
        else e_right += sq;
    }

    if (sum_w > 1e-12) {
        sig.barycenter = (float)(sum_pos_w / sum_w);
        double sum_var = 0.0;
        for (int i = 0; i < dim; ++i) {
            float w = fabsf(vec[i]);
            double d = (double)i - sig.barycenter;
            sum_var += d * d * w;
        }
        sig.dispersion = (float)sqrt(sum_var / sum_w);
    }

    sig.kairos_W_vol = (float)(sqrt(sum_sq) / sqrt((double)dim));
    if (e_left + e_right > 1e-12) {
        sig.kairos_chi = (float)((e_left - e_right) / (e_left + e_right));
    }

    if (in_vec) {
        double dot = 0.0, sq_in = 0.0;
        for (int i = 0; i < dim; ++i) {
            dot += (double)vec[i] * in_vec[i];
            sq_in += (double)in_vec[i] * in_vec[i];
        }
        double norm_prod = sqrt(sum_sq) * sqrt(sq_in);
        sig.kairos_phi = (norm_prod > 1e-12) ? (float)(dot / norm_prod) : 1.0f;
    } else {
        sig.kairos_phi = 1.0f;
    }

    if (sum_sq > 1e-12) {
        double entropy = 0.0;
        for (int i = 0; i < dim; ++i) {
            double p = (double)(vec[i] * vec[i]) / sum_sq;
            if (p > 1e-15) {
                entropy -= p * log(p);
            }
        }
        sig.landauer_entropy = (float)entropy;
    }

    for (int k = 0; k < 16; ++k) {
        sig.top_neurons[k] = -1;
        sig.top_weights[k] = -1.0f;
    }
    for (int i = 0; i < dim; ++i) {
        float w = fabsf(vec[i]);
        for (int k = 0; k < 16; ++k) {
            if (w > sig.top_weights[k]) {
                for (int m = 15; m > k; --m) {
                    sig.top_weights[m] = sig.top_weights[m - 1];
                    sig.top_neurons[m] = sig.top_neurons[m - 1];
                }
                sig.top_weights[k] = w;
                sig.top_neurons[k] = i;
                break;
            }
        }
    }

    return sig;
}

int main(int argc, char** argv) {
    SetConsoleOutputCP(CP_UTF8);

    int domain_choice = 2; /* Défaut : Australie (Canberra) */
    bool compare_lmhead = false;
    bool json_output = false;
    int laser_focus_k = 1000;

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--json")) json_output = true;
        else if (!strcmp(argv[i], "--domain") && i + 1 < argc) domain_choice = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--compare-lmhead")) compare_lmhead = true;
        else if (!strcmp(argv[i], "--k") && i + 1 < argc) laser_focus_k = atoi(argv[++i]);
    }

    int prompt_tokens[MAX_SEQ_LEN];
    int n_prompt = 0;
    const char* domain_title = "";

    if (domain_choice == 1) {
        domain_title = "Géographie (France -> Paris)";
        int d1[] = {32006, 1792, 13, 751, 1808, 707, 425, 27073, 316, 425, 3444, 1577, 32005, 13, 32006, 465, 22137, 13, 997, 27073, 316, 425, 3444, 707};
        n_prompt = sizeof(d1) / sizeof(d1[0]);
        memcpy(prompt_tokens, d1, sizeof(d1));
    } else if (domain_choice == 2) {
        domain_title = "Géographie (Australie -> Canberra)";
        int d2[] = {32006, 1792, 13, 751, 1808, 707, 425, 27073, 316, 301, 29915, 22537, 347, 1577, 32005, 13, 32006, 465, 22137, 13, 997, 27073, 316, 301, 29915, 22537, 347, 707};
        n_prompt = sizeof(d2) / sizeof(d2[0]);
        memcpy(prompt_tokens, d2, sizeof(d2));
    } else if (domain_choice == 3) {
        domain_title = "Chimie (Symbole Fe -> Fer)";
        int d3[] = {32006, 1792, 13, 751, 295, 7877, 15471, 20674, 1387, 263, 1671, 5016, 833, 280, 5169, 1577, 32005, 13, 32006, 465, 22137, 13, 951, 5016, 833, 280, 20674, 1387, 5169, 9982, 4895, 454};
        n_prompt = sizeof(d3) / sizeof(d3[0]);
        memcpy(prompt_tokens, d3, sizeof(d3));
    } else {
        domain_title = "Biochimie (Amylase -> Amidon)";
        int d4[] = {32006, 1792, 13, 751, 295, 3144, 29884, 8204, 4280, 29872, 301, 29915, 4666, 25395, 626, 2904, 559, 4224, 6648, 29899, 29873, 29899, 1808, 1577, 32005, 13, 32006, 465, 22137, 13, 365, 29915, 4666, 25395, 626, 2904, 559, 4224, 6648, 301, 29915};
        n_prompt = sizeof(d4) / sizeof(d4[0]);
        memcpy(prompt_tokens, d4, sizeof(d4));
    }

    const wchar_t* gguf_path = L"C:\\Users\\Christian\\.ollama\\models\\blobs\\sha256-07264f5b41a074562c3fd8bff0e1b7f60ecb4f3441ed5410db35529ee7a207ce";
    const char* vocab_path = "C:\\Users\\Christian\\Documents\\Cerveau Alix\\_Unification_Alix\\src\\alix\\cortex_c99\\tower7b_vocab.bin";

    alix_vocab_t vocab;
    if (compare_lmhead) {
        if (!alix_vocab_load(&vocab, vocab_path)) return 1;
    }

    alix_laser_file_t file;
    if (!alix_laser_open(&file, gguf_path, ALIX_IO_MMAP)) {
        fprintf(stderr, "Erreur ouverture GGUF\n");
        return 1;
    }

    float* k_cache = (float*)calloc((size_t)TOTAL_LAYERS * MAX_SEQ_LEN * DIM_KV, sizeof(float));
    float* v_cache = (float*)calloc((size_t)TOTAL_LAYERS * MAX_SEQ_LEN * DIM_KV, sizeof(float));
    float* x       = (float*)malloc(DIM_MODEL * sizeof(float));
    float* x_in    = (float*)malloc(DIM_MODEL * sizeof(float));
    float* x_norm  = (float*)malloc(DIM_MODEL * sizeof(float));
    float* q_vec   = (float*)malloc(DIM_MODEL * sizeof(float));
    float* attn_o  = (float*)malloc(DIM_MODEL * sizeof(float));
    float* h_act   = (float*)malloc(DIM_FFN * sizeof(float));
    int*   top_idx = (int*)malloc(DIM_FFN * sizeof(int));
    float* logits  = compare_lmhead ? (float*)malloc(VOCAB_SIZE * sizeof(float)) : NULL;

    float* x_in_norm = (float*)malloc(DIM_MODEL * sizeof(float));
    const uint8_t* raw_emb    = (const uint8_t*)alix_laser_mmap_pointer(&file, TOWER7B_TOKEN_EMBD_OFF);
    const float*   w_out_norm = (const float*)alix_laser_mmap_pointer(&file, TOWER7B_OUTPUT_NORM_OFF);
    const uint8_t* raw_out    = compare_lmhead ? (const uint8_t*)alix_laser_mmap_pointer(&file, TOWER7B_OUTPUT_OFF) : NULL;

    /* Chargement ou calcul du cache KV */
    char kv_cache_file[512];
    snprintf(kv_cache_file, sizeof(kv_cache_file), "C:\\Users\\Christian\\Documents\\Cerveau Alix\\_Unification_Alix\\src\\alix\\cortex_c99\\tower7b_kv_domain%d.bin", domain_choice);
    size_t kv_bytes = (size_t)TOTAL_LAYERS * MAX_SEQ_LEN * DIM_KV * sizeof(float);
    FILE* fkv = fopen(kv_cache_file, "rb");
    bool loaded_kv = false;
    if (fkv) {
        fread(k_cache, 1, kv_bytes, fkv);
        fread(v_cache, 1, kv_bytes, fkv);
        fclose(fkv);
        loaded_kv = true;
    }

    double t0 = get_time_ms();

    /* 1. Prefill des tokens si pas en cache */
    if (!loaded_kv && n_prompt > 1) {
        for (int pos = 0; pos < n_prompt - 1; ++pos) {
            int tid = prompt_tokens[pos];
            const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_emb + (size_t)tid * ROW_BYTES_4096_Q4K);
            for (int sb = 0; sb < BLOCKS_PER_ROW_4096; ++sb) {
                dequantize_q4_K_block(&emb_row[sb], x + sb * 256);
            }
            for (int l = 0; l < CUTOFF_LAYERS; ++l) {
                forward_one_layer_landauer(&file, l, pos, x, k_cache, v_cache, DIM_FFN, 0, x_norm, q_vec, attn_o, h_act, top_idx);
            }
        }
        fkv = fopen(kv_cache_file, "wb");
        if (fkv) {
            fwrite(k_cache, 1, kv_bytes, fkv);
            fwrite(v_cache, 1, kv_bytes, fkv);
            fclose(fkv);
        }
    }

    /* 2. Dernier token : point de résonance */
    int pos = n_prompt - 1;
    int tid = prompt_tokens[pos];
    const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_emb + (size_t)tid * ROW_BYTES_4096_Q4K);
    for (int sb = 0; sb < BLOCKS_PER_ROW_4096; ++sb) {
        dequantize_q4_K_block(&emb_row[sb], x + sb * 256);
    }
    memcpy(x_in, x, DIM_MODEL * sizeof(float));

    double tl0 = get_time_ms();
    for (int l = 0; l < CUTOFF_LAYERS; ++l) {
        int k_layer = laser_focus_k;
        int resc = 2;
        if (l < 8) k_layer = 160;
        forward_one_layer_landauer(&file, l, pos, x, k_cache, v_cache, k_layer, resc, x_norm, q_vec, attn_o, h_act, top_idx);
    }
    double t_layers = get_time_ms() - tl0;

    /* 3. 🏛️ NORMALISATION & EXTRACTION TOPOLOGIQUE PURE HEIMDALL / KAIROS (ZÉRO LM_HEAD) */
    alix_rmsnorm(x, w_out_norm, x_norm, DIM_MODEL);
    alix_rmsnorm(x_in, w_out_norm, x_in_norm, DIM_MODEL);

    /* Sauvegarde de l'état géométrique invariant sur disque */
    char state_file[512];
    snprintf(state_file, sizeof(state_file), "C:\\Users\\Christian\\Documents\\Cerveau Alix\\_Unification_Alix\\src\\alix\\cortex_c99\\domain%d_state.bin", domain_choice);
    FILE* fstate = fopen(state_file, "wb");
    if (fstate) {
        fwrite(x_norm, sizeof(float), DIM_MODEL, fstate);
        fclose(fstate);
    }

    double tt0 = get_time_ms();
    alix_topologie_sig_t sig_residu = calculer_signature_topologique(x_norm, DIM_MODEL, x_in_norm);
    alix_topologie_sig_t sig_ffn    = calculer_signature_topologique(h_act, DIM_FFN, NULL);
    double t_topo_ms = get_time_ms() - tt0;

    /* 4. LM_Head baseline optionnelle pour vérification */
    double t_lmhead_ms = 0.0;
    int best_token_id = -1;
    float best_logit = -1e30f;
    char best_str[64] = "";

    if (compare_lmhead) {
        double th0 = get_time_ms();
        for (int v = 0; v < VOCAB_SIZE; ++v) logits[v] = -1e30f;
        run_parallel_ex(VOCAB_SIZE, 6, x_norm, raw_out, NULL, NULL, 14, logits, NULL, NULL, NULL, 0, 1.0f);
        for (int v = 0; v < VOCAB_SIZE; ++v) {
            if (is_parasitic_token(&vocab, v)) continue;
            if (logits[v] > best_logit) {
                best_logit = logits[v];
                best_token_id = v;
            }
        }
        alix_vocab_get_token(&vocab, best_token_id, best_str, sizeof(best_str));
        t_lmhead_ms = get_time_ms() - th0;
    }

    double total_ms = get_time_ms() - t0;

    if (json_output) {
        printf("{\n");
        printf("  \"status\": \"ok\",\n");
        printf("  \"domain\": \"%s\",\n", domain_title);
        printf("  \"timing\": {\"layers_ms\": %.2f, \"topo_ms\": %.4f, \"lmhead_ms\": %.2f, \"total_ms\": %.2f},\n",
               t_layers, t_topo_ms, t_lmhead_ms, total_ms);
        printf("  \"residu\": {\n");
        printf("    \"barycenter\": %.2f,\n", sig_residu.barycenter);
        printf("    \"dispersion\": %.2f,\n", sig_residu.dispersion);
        printf("    \"W_vol\": %.4f,\n", sig_residu.kairos_W_vol);
        printf("    \"chi\": %.4f,\n", sig_residu.kairos_chi);
        printf("    \"phi\": %.4f,\n", sig_residu.kairos_phi);
        printf("    \"entropy\": %.4f,\n", sig_residu.landauer_entropy);
        printf("    \"top_neurons\": [");
        for (int k = 0; k < 16; ++k) printf("%d%s", sig_residu.top_neurons[k], (k < 15) ? "," : "");
        printf("]\n");
        printf("  },\n");
        printf("  \"ffn_layer28\": {\n");
        printf("    \"barycenter\": %.2f,\n", sig_ffn.barycenter);
        printf("    \"dispersion\": %.2f,\n", sig_ffn.dispersion);
        printf("    \"W_vol\": %.4f,\n", sig_ffn.kairos_W_vol);
        printf("    \"chi\": %.4f,\n", sig_ffn.kairos_chi);
        printf("    \"entropy\": %.4f,\n", sig_ffn.landauer_entropy);
        printf("    \"top_neurons\": [");
        for (int k = 0; k < 16; ++k) printf("%d%s", sig_ffn.top_neurons[k], (k < 15) ? "," : "");
        printf("]\n");
        printf("  }");
        if (compare_lmhead) {
            printf(",\n  \"lm_head_baseline\": {\"token_id\": %d, \"token_str\": \"%s\", \"logit\": %.2f}\n",
                   best_token_id, best_str, best_logit);
        } else {
            printf("\n");
        }
        printf("}\n");
    } else {
        printf("==============================================================================\n");
        printf("  🏛️⚡ ALIX SCALPEL TOPOLOGIQUE : LECTURE SPATIALE PURE (HEIMDALL / KAIROS)\n");
        printf("==============================================================================\n");
        printf("  • Domaine / Requête : %s\n", domain_title);
        printf("  • Strates Lues      : Couches L00 à L%02d (Arrêt avant couches cosmétiques)\n", CUTOFF_LAYERS - 1);
        printf("  • Foyer Laser       : %d neurones (Landauer L08..L28)\n", laser_focus_k);
        printf("  • Chronométrage     : Layers: %.2f ms | ⚡ Extraction Topologique: %.4f ms (TOTAL: %.2f ms)\n",
               t_layers, t_topo_ms, total_ms);
        printf("------------------------------------------------------------------------------\n");
        printf("  📐 1. SIGNATURE GÉOMÉTRIQUE DU FLUX RÉSIDUEL (R^4096) :\n");
        printf("     - Barycentre Spatial : %.2f (dispersion σ = %.2f)\n", sig_residu.barycenter, sig_residu.dispersion);
        printf("     - Triplet KAIROS     : W_vol = %.4f | χ = %+.4f | Φ = %.4f\n",
               sig_residu.kairos_W_vol, sig_residu.kairos_chi, sig_residu.kairos_phi);
        printf("     - Entropie Landauer  : S = %.4f nats\n", sig_residu.landauer_entropy);
        printf("     - Top-8 Résonances   : ");
        for (int k = 0; k < 8; ++k) printf("[%d: %.2f] ", sig_residu.top_neurons[k], sig_residu.top_weights[k]);
        printf("\n");
        printf("------------------------------------------------------------------------------\n");
        printf("  🧬 2. RÉSONANCE DE LA COUCHE FFN MÉMOIRE (R^11008) :\n");
        printf("     - Barycentre Spatial : %.2f (dispersion σ = %.2f)\n", sig_ffn.barycenter, sig_ffn.dispersion);
        printf("     - Triplet KAIROS     : W_vol = %.4f | χ = %+.4f\n", sig_ffn.kairos_W_vol, sig_ffn.kairos_chi);
        printf("     - Entropie Mémoire   : S = %.4f nats\n", sig_ffn.landauer_entropy);
        printf("     - Neurones Actifs    : ");
        for (int k = 0; k < 8; ++k) printf("#%d (%.2f) ", sig_ffn.top_neurons[k], sig_ffn.top_weights[k]);
        printf("\n");
        if (compare_lmhead) {
            printf("------------------------------------------------------------------------------\n");
            printf("  🔍 3. BASELINE LM_HEAD (POUR COMPARAISON SEULEMENT - %.2f ms) :\n", t_lmhead_ms);
            printf("     - Token prédit : '%s' (ID %d, logit: %.2f)\n", best_str, best_token_id, best_logit);
        }
        printf("==============================================================================\n");
    }

    alix_laser_close(&file);
    free(k_cache); free(v_cache); free(x); free(x_in); free(x_norm); free(x_in_norm);
    free(q_vec); free(attn_o); free(h_act); free(top_idx);
    if (logits) free(logits);
    return 0;
}
