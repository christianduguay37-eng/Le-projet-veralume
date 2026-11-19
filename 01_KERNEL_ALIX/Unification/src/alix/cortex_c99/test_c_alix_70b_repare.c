/**
 * ============================================================================
 *   🏛️⚡ C-ALIX SUR TITAN LLAMA-3.3-70B (CLÉ USB E:) — VERSION RÉPARÉE !
 *   Fichier : test_c_alix_70b_repare.c
 * ============================================================================
 *   Intègre les découvertes du banc comparatif 7B (ProSparse <-> Tower-7B) :
 *     1. `dequantize_q4_K_block` et `dequantize_q4_K_single` corrigés (32 nibbles
 *        bas puis 32 nibbles hauts, au lieu de l'entrelacement erroné).
 *     2. `alix_apply_rope_gguf` corrigé sur les paires adjacentes (2*i, 2*i+1)
 *        conformément à la permutation GGUF de `attn_q` et `attn_k`.
 *     3. Types exacts `Q4_K` (12), `Q5_K` (13), `Q6_K` (14) lus depuis
 *        `alix_llama70b_full_offsets.h`.
 *     4. Multithreading Win32 sur les 8 cœurs du Lunar Lake 258V.
 *     5. Coupe Stratigraphique + HLS (1 couche sur 3) + Conservation d'énergie.
 * ============================================================================
 */

#include "alix_laser_io.h"
#include "alix_llama70b_full_offsets.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <string.h>

#define DIM_MODEL           8192
#define DIM_FFN             28672
#define NUM_LAYERS          80
#define NUM_HEADS           64
#define HEAD_DIM            128
#define NUM_KV_HEADS        8
#define DIM_KV              1024
#define GQA_GROUP           8
#define MAX_SEQ_LEN         32
#define BLOCKS_PER_ROW_8192 32
#define BLOCKS_PER_ROW_DOWN 112
#define ROW_BYTES_Q4K       4608
#define ROW_BYTES_Q5K       5632
#define ROW_BYTES_Q6K       6720
#define ROW_BYTES_DOWN_Q4K  16128
#define ROW_BYTES_DOWN_Q6K  23520
#define ROPE_THETA          500000.0f
#define EPS_RMSNORM         1e-5f
#define VOCAB_SIZE          128256
#define NUM_THREADS         8

#pragma pack(push, 1)
typedef struct {
    uint16_t d;
    uint16_t dmin;
    uint8_t  scales[12];
    uint8_t  qs[128];
} block_q4_K_t;

typedef struct {
    uint16_t d;
    uint16_t dmin;
    uint8_t  scales[12];
    uint8_t  qh[32];
    uint8_t  qs[128];
} block_q5_K_t;

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
 * 1. DÉQUANTIFICATION Q4_K EXACTE (32 NIBBLES BAS / 32 NIBBLES HAUTS)
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
    int sb = idx / 32;
    int l  = idx % 32;
    int j  = sb / 2;
    float d_sub = d * (float)sc[sb];
    float m_sub = dmin * (float)m[sb];
    uint8_t byte_val = b->qs[j * 32 + l];
    uint8_t q_val = (sb % 2 == 0) ? (byte_val & 0x0F) : (byte_val >> 4);
    return d_sub * (float)q_val - m_sub;
}

static inline void dequantize_q5_K_block(const block_q5_K_t* b, float* out) {
    float d = fp16_to_fp32(b->d);
    float dmin = fp16_to_fp32(b->dmin);
    uint8_t sc[8], m[8];
    for (int j = 0; j < 4; ++j) {
        sc[j]     = b->scales[j] & 63;
        m[j]      = b->scales[j + 4] & 63;
        sc[j + 4] = (b->scales[j + 8] & 15) | ((b->scales[j] >> 6) << 4);
        m[j + 4]  = (b->scales[j + 8] >> 4) | ((b->scales[j + 4] >> 6) << 4);
    }
    const uint8_t* qh = b->qh;
    const uint8_t* qs = b->qs;
    for (int sb = 0; sb < 8; ++sb) {
        float d_sub = d * (float)sc[sb];
        float m_sub = dmin * (float)m[sb];
        int qs_offset = (sb / 2) * 32;
        int shift = (sb % 2 == 0) ? 0 : 4;
        for (int l = 0; l < 32; ++l) {
            uint8_t ql = (qs[qs_offset + l] >> shift) & 0x0F;
            uint8_t h_bit = (qh[l] >> sb) & 1;
            uint8_t q = ql | (h_bit << 4);
            out[sb * 32 + l] = d_sub * (float)q - m_sub;
        }
    }
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

static inline float dot_q4_K_row8192(const block_q4_K_t* row, const float* x) {
    float sum = 0.0f;
    float buf[256];
    for (int sb = 0; sb < BLOCKS_PER_ROW_8192; ++sb) {
        dequantize_q4_K_block(&row[sb], buf);
        const float* xs = x + sb * 256;
        for (int i = 0; i < 256; ++i) sum += buf[i] * xs[i];
    }
    return sum;
}

static inline float dot_q5_K_row8192(const block_q5_K_t* row, const float* x) {
    float sum = 0.0f;
    float buf[256];
    for (int sb = 0; sb < BLOCKS_PER_ROW_8192; ++sb) {
        dequantize_q5_K_block(&row[sb], buf);
        const float* xs = x + sb * 256;
        for (int i = 0; i < 256; ++i) sum += buf[i] * xs[i];
    }
    return sum;
}

static inline float dot_q6_K_row8192(const block_q6_K_t* row, const float* x) {
    float sum = 0.0f;
    float buf[256];
    for (int sb = 0; sb < BLOCKS_PER_ROW_8192; ++sb) {
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

/* ============================================================================
 * 2. ROTATION ROPE GGUF EXACTE (PAIRES ADJACENTES 2*i, 2*i+1)
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

/* ============================================================================
 * POOL MULTITHREAD WIN32 (8 CŒURS) POUR LE 70B
 * ============================================================================ */
typedef struct {
    int start_row;
    int end_row;
    int task_type; /* 1=Q, 2=KV, 3=Wo, 4=GateUp, 5=DownSparse, 6=DownDense */
    const float* x_norm;
    const uint8_t* raw_a;
    const uint8_t* raw_b;
    int type_b;
    float* out_a;
    float* out_b;
    const int* top_idx;
    int k_use;
    float alpha;
} mt70_task_t;

static DWORD WINAPI worker70_proc(LPVOID param) {
    mt70_task_t* t = (mt70_task_t*)param;
    if (t->task_type == 1) { /* Q (8192 lignes) */
        for (int r = t->start_row; r < t->end_row; ++r) {
            const block_q4_K_t* q_row = (const block_q4_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_Q4K);
            t->out_a[r] = dot_q4_K_row8192(q_row, t->x_norm);
        }
    } else if (t->task_type == 2) { /* K, V (1024 lignes GQA) */
        for (int r = t->start_row; r < t->end_row; ++r) {
            const block_q4_K_t* k_row = (const block_q4_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_Q4K);
            t->out_a[r] = dot_q4_K_row8192(k_row, t->x_norm);
            if (t->type_b == 14) {
                const block_q6_K_t* v_row = (const block_q6_K_t*)(t->raw_b + (size_t)r * ROW_BYTES_Q6K);
                t->out_b[r] = dot_q6_K_row8192(v_row, t->x_norm);
            } else if (t->type_b == 13) {
                const block_q5_K_t* v_row = (const block_q5_K_t*)(t->raw_b + (size_t)r * ROW_BYTES_Q5K);
                t->out_b[r] = dot_q5_K_row8192(v_row, t->x_norm);
            } else {
                const block_q4_K_t* v_row = (const block_q4_K_t*)(t->raw_b + (size_t)r * ROW_BYTES_Q4K);
                t->out_b[r] = dot_q4_K_row8192(v_row, t->x_norm);
            }
        }
    } else if (t->task_type == 3) { /* Wo (8192 lignes) */
        for (int r = t->start_row; r < t->end_row; ++r) {
            const block_q4_K_t* wo_row = (const block_q4_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_Q4K);
            t->out_a[r] += dot_q4_K_row8192(wo_row, t->x_norm);
        }
    } else if (t->task_type == 4) { /* Gate + Up (28672 lignes) */
        for (int n = t->start_row; n < t->end_row; ++n) {
            const block_q4_K_t* g_row = (const block_q4_K_t*)(t->raw_a + (size_t)n * ROW_BYTES_Q4K);
            const block_q4_K_t* u_row = (const block_q4_K_t*)(t->raw_b + (size_t)n * ROW_BYTES_Q4K);
            float g = dot_q4_K_row8192(g_row, t->x_norm);
            float u = dot_q4_K_row8192(u_row, t->x_norm);
            float s = g / (1.0f + expf(-g));
            t->out_a[n] = s * u;
        }
    } else if (t->task_type == 5) { /* Down Sparse (K colonnes sur 8192 lignes) */
        for (int r = t->start_row; r < t->end_row; ++r) {
            float sum_d = 0.0f;
            if (t->type_b == 14) {
                const block_q6_K_t* d_row = (const block_q6_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_DOWN_Q6K);
                for (int i = 0; i < t->k_use; ++i) {
                    int n_id = t->top_idx[i];
                    sum_d += t->x_norm[n_id] * dequantize_q6_K_single(&d_row[n_id / 256], n_id % 256);
                }
            } else {
                const block_q4_K_t* d_row = (const block_q4_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_DOWN_Q4K);
                for (int i = 0; i < t->k_use; ++i) {
                    int n_id = t->top_idx[i];
                    sum_d += t->x_norm[n_id] * dequantize_q4_K_single(&d_row[n_id / 256], n_id % 256);
                }
            }
            t->out_a[r] += sum_d * t->alpha;
        }
    } else if (t->task_type == 6) { /* Down Dense (28672 colonnes sur 8192 lignes) */
        float buf[256];
        for (int r = t->start_row; r < t->end_row; ++r) {
            float sum_d = 0.0f;
            if (t->type_b == 14) {
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
    }
    return 0;
}

static void run_parallel70(int total_rows, int task_type, const float* x_norm,
                           const uint8_t* raw_a, const uint8_t* raw_b, int type_b,
                           float* out_a, float* out_b, const int* top_idx, int k_use, float alpha) {
    HANDLE threads[NUM_THREADS];
    mt70_task_t tasks[NUM_THREADS];
    int chunk = (total_rows + NUM_THREADS - 1) / NUM_THREADS;
    for (int i = 0; i < NUM_THREADS; ++i) {
        tasks[i].start_row = i * chunk;
        tasks[i].end_row   = (i + 1) * chunk;
        if (tasks[i].end_row > total_rows) tasks[i].end_row = total_rows;
        tasks[i].task_type = task_type;
        tasks[i].x_norm    = x_norm;
        tasks[i].raw_a     = raw_a;
        tasks[i].raw_b     = raw_b;
        tasks[i].type_b    = type_b;
        tasks[i].out_a     = out_a;
        tasks[i].out_b     = out_b;
        tasks[i].top_idx   = top_idx;
        tasks[i].k_use     = k_use;
        tasks[i].alpha     = alpha;
        threads[i] = CreateThread(NULL, 0, worker70_proc, &tasks[i], 0, NULL);
    }
    WaitForMultipleObjects(NUM_THREADS, threads, TRUE, INFINITE);
    for (int i = 0; i < NUM_THREADS; ++i) CloseHandle(threads[i]);
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
    const char* raw = v->text_blob + off;
    if (len >= 2 && (unsigned char)raw[0] == 0xC4 && (unsigned char)raw[1] == 0xA0) {
        buf[0] = ' ';
        size_t rest = len - 2;
        if (rest > buf_max - 2) rest = buf_max - 2;
        memcpy(buf + 1, raw + 2, rest);
        buf[1 + rest] = '\0';
    } else {
        memcpy(buf, raw, len);
        buf[len] = '\0';
    }
}

void forward_one_layer_70b(
    alix_laser_file_t* file,
    int l,
    int pos,
    float* x,
    float* k_cache,
    float* v_cache,
    int k_use, /* 0 = skip FFN (HLS), DIM_FFN = Dense, < DIM_FFN = Top-K + sqrt(alpha) */
    float* x_norm,
    float* q_vec,
    float* attn_o,
    float* h_act,
    int* top_idx
) {
    const alix_llama70b_full_layer_offsets_t* L = &LLAMA70B_FULL_OFFSETS[l];

    const float* w_anorm = (const float*)alix_laser_mmap_pointer(file, L->attn_norm_off);
    alix_rmsnorm(x, w_anorm, x_norm, DIM_MODEL);

    const uint8_t* raw_q = (const uint8_t*)alix_laser_mmap_pointer(file, L->attn_q_off);
    const uint8_t* raw_k = (const uint8_t*)alix_laser_mmap_pointer(file, L->attn_k_off);
    const uint8_t* raw_v = (const uint8_t*)alix_laser_mmap_pointer(file, L->attn_v_off);

    float* k_slot = k_cache + ((size_t)l * MAX_SEQ_LEN + pos) * DIM_KV;
    float* v_slot = v_cache + ((size_t)l * MAX_SEQ_LEN + pos) * DIM_KV;

    run_parallel70(DIM_MODEL, 1, x_norm, raw_q, NULL, 0, q_vec, NULL, NULL, 0, 1.0f);
    run_parallel70(DIM_KV,    2, x_norm, raw_k, raw_v, L->attn_v_type, k_slot, v_slot, NULL, 0, 1.0f);

    alix_apply_rope_gguf(q_vec,  NUM_HEADS,    HEAD_DIM, pos, ROPE_THETA);
    alix_apply_rope_gguf(k_slot, NUM_KV_HEADS, HEAD_DIM, pos, ROPE_THETA);

    float scale = 1.0f / sqrtf((float)HEAD_DIM);
    memset(attn_o, 0, DIM_MODEL * sizeof(float));

    for (int h = 0; h < NUM_HEADS; ++h) {
        int kv_h = h / GQA_GROUP;
        const float* q_h = q_vec + h * HEAD_DIM;
        float scores[MAX_SEQ_LEN];
        float max_s = -1e30f;
        for (int t = 0; t <= pos; ++t) {
            const float* k_ht = k_cache + ((size_t)l * MAX_SEQ_LEN + t) * DIM_KV + kv_h * HEAD_DIM;
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
            const float* v_ht = v_cache + ((size_t)l * MAX_SEQ_LEN + t) * DIM_KV + kv_h * HEAD_DIM;
            for (int d = 0; d < HEAD_DIM; ++d) out_h[d] += w * v_ht[d];
        }
    }

    const uint8_t* raw_wo = (const uint8_t*)alix_laser_mmap_pointer(file, L->attn_output_off);
    run_parallel70(DIM_MODEL, 3, attn_o, raw_wo, NULL, 0, x, NULL, NULL, 0, 1.0f);

    if (k_use <= 0) return; /* Saut HLS (Attention pure) */

    const float* w_fnorm = (const float*)alix_laser_mmap_pointer(file, L->ffn_norm_off);
    alix_rmsnorm(x, w_fnorm, x_norm, DIM_MODEL);

    const uint8_t* raw_gate = (const uint8_t*)alix_laser_mmap_pointer(file, L->ffn_gate_off);
    const uint8_t* raw_up   = (const uint8_t*)alix_laser_mmap_pointer(file, L->ffn_up_off);
    const uint8_t* raw_down = (const uint8_t*)alix_laser_mmap_pointer(file, L->ffn_down_off);

    if (k_use < DIM_FFN) {
        /* VRAI LASER SUR USB : Ne lire que k_use lignes dans Gate et Up (pas les 28 672 !)
           Évite de lire 21 Go par token sur la clé USB et garde les 7.5 Go d'attention 100% en RAM ! */
        int step_n = DIM_FFN / k_use;
        for (int i = 0; i < k_use; ++i) {
            int n_id = (i * step_n + (l * 13)) % DIM_FFN;
            top_idx[i] = n_id;
            const block_q4_K_t* g_row = (const block_q4_K_t*)(raw_gate + (size_t)n_id * ROW_BYTES_Q4K);
            const block_q4_K_t* u_row = (const block_q4_K_t*)(raw_up   + (size_t)n_id * ROW_BYTES_Q4K);
            float g = dot_q4_K_row8192(g_row, x_norm);
            float u = dot_q4_K_row8192(u_row, x_norm);
            float s = g / (1.0f + expf(-g));
            h_act[n_id] = s * u;
        }
        float alpha = 1.35f;
        run_parallel70(DIM_MODEL, 5, h_act, raw_down, NULL, L->ffn_down_type, x, NULL, top_idx, k_use, alpha);
    } else {
        run_parallel70(DIM_FFN, 4, x_norm, raw_gate, raw_up, 0, h_act, NULL, NULL, 0, 1.0f);
        run_parallel70(DIM_MODEL, 6, h_act, raw_down, NULL, L->ffn_down_type, x, NULL, NULL, 0, 1.0f);
    }
}

int main(void) {
    SetConsoleOutputCP(CP_UTF8);
    setvbuf(stdout, NULL, _IONBF, 0);

    const wchar_t* usb_path = L"E:\\Modeles_4e_Etage\\Llama-3.3-70B-Instruct-Q4_K_M.gguf";
    const char* vocab_path  = "C:\\Users\\Christian\\Documents\\Cerveau Alix\\_Unification_Alix\\src\\alix\\cortex_c99\\llama3_vocab.bin";

    alix_vocab_t vocab;
    if (!alix_vocab_load(&vocab, vocab_path)) { printf("Erreur vocab\n"); return 1; }

    alix_laser_file_t file;
    if (!alix_laser_open(&file, usb_path, ALIX_IO_MMAP)) { printf("Erreur mmap USB\n"); return 1; }

    /* Prompt : "<|begin_of_text|>La capitale de la France est" (8 tokens) */
    int prompt_tokens[] = { 128000, 8921, 6864, 68, 409, 1208, 9822, 1826 };
    int n_prompt = 8;

    printf("==============================================================================\n");
    printf("  🏛️⚡ C-ALIX SUR TITAN LLAMA-3.3-70B (CLÉ USB E:) — Q4_K + ROPE RÉPARÉS !\n");
    printf("  Prompt : \"La capitale de la France est\" (8 tokens, 80 couches)\n");
    printf("==============================================================================\n\n");

    float* k_cache = (float*)calloc((size_t)NUM_LAYERS * MAX_SEQ_LEN * DIM_KV, sizeof(float));
    float* v_cache = (float*)calloc((size_t)NUM_LAYERS * MAX_SEQ_LEN * DIM_KV, sizeof(float));
    float* x       = (float*)malloc(DIM_MODEL * sizeof(float));
    float* x_norm  = (float*)malloc(DIM_MODEL * sizeof(float));
    float* q_vec   = (float*)malloc(DIM_MODEL * sizeof(float));
    float* attn_o  = (float*)malloc(DIM_MODEL * sizeof(float));
    float* h_act   = (float*)malloc(DIM_FFN * sizeof(float));
    int*   top_idx = (int*)malloc(DIM_FFN * sizeof(int));

    const uint8_t* raw_emb    = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_TOKEN_EMBD_OFFSET);
    const float*   w_out_norm = (const float*)alix_laser_mmap_pointer(&file, LLAMA70B_OUTPUT_NORM_OFFSET);
    const uint8_t* raw_out    = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_OUTPUT_OFFSET);

    double t_start = get_time_ms();

    for (int pos = 0; pos < n_prompt; ++pos) {
        double t_tok = get_time_ms();
        int tid = prompt_tokens[pos];
        const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_emb + (size_t)tid * ROW_BYTES_Q4K);
        for (int sb = 0; sb < BLOCKS_PER_ROW_8192; ++sb) {
            dequantize_q4_K_block(&emb_row[sb], x + sb * 256);
        }

        int is_last = (pos == n_prompt - 1);

        for (int l = 0; l < NUM_LAYERS; ++l) {
            int k_layer = 80;
            if (!is_last) {
                /* Prefill accéléré avec coupe HLS 1 couche sur 3 au milieu + 80 neurones */
                if (l >= 10 && l < 70 && (l % 3 != 0)) k_layer = 0;
                else k_layer = 80;
            } else {
                /* Dernier token : Profil Stratigraphique C-Alix + HLS */
                if (l < 16)       k_layer = 80;
                else if (l < 60)  k_layer = (l % 2 == 0) ? 160 : 0;
                else              k_layer = 160;
            }
            forward_one_layer_70b(&file, l, pos, x, k_cache, v_cache, k_layer, x_norm, q_vec, attn_o, h_act, top_idx);
        }
        printf("  [Token %d/%d pos=%d tid=%d] 80 couches franchies en %.2f s\n", pos + 1, n_prompt, pos, tid, (get_time_ms() - t_tok) / 1000.0);
    }

    alix_rmsnorm(x, w_out_norm, x_norm, DIM_MODEL);

    int top10_tid[10] = {0};
    float top10_lg[10];
    for (int i = 0; i < 10; ++i) top10_lg[i] = -1e30f;

    float lg_paris = -1e30f;
    int rank_paris = 1;

    for (int v = 0; v < VOCAB_SIZE; ++v) {
        const block_q6_K_t* out_row = (const block_q6_K_t*)(raw_out + (size_t)v * ROW_BYTES_Q6K);
        float lg = dot_q6_K_row8192(out_row, x_norm);
        if (v == 12366) lg_paris = lg;
        for (int k = 0; k < 10; ++k) {
            if (lg > top10_lg[k]) {
                for (int s = 9; s > k; --s) {
                    top10_lg[s] = top10_lg[s - 1];
                    top10_tid[s] = top10_tid[s - 1];
                }
                top10_lg[k] = lg;
                top10_tid[k] = v;
                break;
            }
        }
    }
    for (int v = 0; v < VOCAB_SIZE; ++v) {
        const block_q6_K_t* out_row = (const block_q6_K_t*)(raw_out + (size_t)v * ROW_BYTES_Q6K);
        float lg = dot_q6_K_row8192(out_row, x_norm);
        if (lg > lg_paris) rank_paris++;
    }

    printf("\n==============================================================================\n");
    printf("  🏆 RÉSULTAT TITAN LLAMA-3.3-70B (CLÉ USB E:) EN %.2f s :\n", (get_time_ms() - t_start) / 1000.0);
    printf("  • ' Paris' (#12366) : Logit = %6.2f | Rang = #%d / %d\n", lg_paris, rank_paris, VOCAB_SIZE);
    printf("  • Top-10 sur 128 256 tokens :\n");
    for (int k = 0; k < 10; ++k) {
        char tbuf[128];
        alix_vocab_get_token(&vocab, top10_tid[k], tbuf, sizeof(tbuf));
        printf("    #%2d : Token %6d | Logit = %6.2f | '%s'\n", k + 1, top10_tid[k], top10_lg[k], tbuf);
    }
    printf("==============================================================================\n");

    alix_laser_close(&file);
    return 0;
}
