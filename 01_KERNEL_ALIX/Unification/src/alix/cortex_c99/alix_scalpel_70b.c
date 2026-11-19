/**
 * ============================================================================
 *   🏛️⚡ ALIX SCALPEL 70B — SONDE TRANSVERSALE LANDAUER SUR TITAN 70B
 *   Module : alix_scalpel_70b.c
 * ============================================================================
 *   Auteurs   : Christian Duguay & Alix (VERALUME x KAIROS)
 *   Substrat  : Windows 11 x86-64 / Intel Lunar Lake Core Ultra 7 258V (32 Go RAM)
 *   Cible     : Llama-3.3-70B-Instruct-Q4_K_M.gguf (42.5 Go sur clé USB E:\)
 *   Modes :
 *     • Mode 1 : Option 1 (Criblage rapide Coarse-to-Fine dynamique)
 *     • Mode 2 : Option 2 (Fovéa géométrique de Christian pré-identifiée)
 * ============================================================================
 */

#include "alix_laser_io.h"
#include "alix_llama70b_full_offsets.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <math.h>
#include <windows.h>

#define DIM_MODEL               8192
#define DIM_FFN                 28672
#define NUM_HEADS               64
#define HEAD_DIM                128
#define NUM_KV_HEADS            8
#define DIM_KV                  1024
#define GQA_GROUP               8
#define MAX_SEQ_LEN             128
#define TOTAL_LAYERS            80
#define DEFAULT_CUTOFF_LAYERS   77  /* Arrêt après L76 (zappe les 3 couches cosmétiques L77..L79) */
#define VOCAB_SIZE              128256
#define ROPE_THETA              500000.0f
#define EPS_RMSNORM             1e-5f
#define NUM_THREADS             8

#define BLOCKS_PER_ROW_8192     32
#define BLOCKS_PER_ROW_DOWN     112
#define ROW_BYTES_8192_Q4K      (32 * 144)
#define ROW_BYTES_8192_Q5K      (32 * 176)
#define ROW_BYTES_8192_Q6K      (32 * 210)
#define ROW_BYTES_DOWN_Q4K      (112 * 144)
#define ROW_BYTES_DOWN_Q6K      (112 * 210)

/* Fovéa d'acier de Christian pour France (D1 - L00) */
static const int FOVEA_GEO_FRANCE_80[80] = {
    3552, 715, 2199, 2996, 1188, 1035, 2392, 1855, 545, 3267,
    1436, 2866, 1858, 2159, 540, 2465, 719, 2770, 3459, 1484,
    1020, 1390, 2341, 1547, 780, 2104, 1926, 2858, 1824, 401,
    2419, 993, 2835, 149, 2809, 42, 923, 60, 452, 190,
    3201, 2596, 1371, 1333, 1932, 1054, 2490, 2246, 3393, 1408,
    2845, 113, 2301, 1021, 3061, 24152, 3499, 1650, 1802, 3180,
    1509, 2241, 2794, 1463, 2975, 326, 2202, 602, 368, 2683,
    3398, 3294, 577, 3409, 2401, 2791, 3583, 67, 660, 3171
};

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

/* Produit scalaire rapide sur 512 dimensions (2 blocs de 256) pour le criblage coarse */
static inline float dot_q4_K_row512(const block_q4_K_t* row_blocks, const float* x) {
    float total = 0.0f;
    for (int sb = 0; sb < 2; ++sb) {
        const block_q4_K_t* b = &row_blocks[sb];
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
        const float* xs = x + sb * 256;
        float b_sum = 0.0f;
        for (int j = 0; j < 4; ++j) {
            float d1 = d * (float)sc[2 * j];
            float m1 = dmin * (float)m[2 * j];
            float d2 = d * (float)sc[2 * j + 1];
            float m2 = dmin * (float)m[2 * j + 1];
            for (int l = 0; l < 32; ++l) {
                uint8_t byte_val = q[j * 32 + l];
                float v1 = d1 * (float)(byte_val & 0x0F) - m1;
                float v2 = d2 * (float)(byte_val >> 4)   - m2;
                b_sum += v1 * xs[j * 64 + l] + v2 * xs[j * 64 + 32 + l];
            }
        }
        total += b_sum;
    }
    return total;
}

static inline float dot_q4_K_row8192(const block_q4_K_t* row_blocks, const float* x) {
    float total = 0.0f;
    for (int sb = 0; sb < BLOCKS_PER_ROW_8192; ++sb) {
        const block_q4_K_t* b = &row_blocks[sb];
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
        const float* xs = x + sb * 256;
        float b_sum = 0.0f;
        for (int j = 0; j < 4; ++j) {
            float d1 = d * (float)sc[2 * j];
            float m1 = dmin * (float)m[2 * j];
            float d2 = d * (float)sc[2 * j + 1];
            float m2 = dmin * (float)m[2 * j + 1];
            for (int l = 0; l < 32; ++l) {
                uint8_t byte_val = q[j * 32 + l];
                float v1 = d1 * (float)(byte_val & 0x0F) - m1;
                float v2 = d2 * (float)(byte_val >> 4)   - m2;
                b_sum += v1 * xs[j * 64 + l] + v2 * xs[j * 64 + 32 + l];
            }
        }
        total += b_sum;
    }
    return total;
}

static inline float dot_q5_K_row8192(const block_q5_K_t* row_blocks, const float* x) {
    float total = 0.0f;
    for (int sb = 0; sb < BLOCKS_PER_ROW_8192; ++sb) {
        const block_q5_K_t* b = &row_blocks[sb];
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
        const float* xs = x + sb * 256;
        float b_sum = 0.0f;
        for (int s = 0; s < 8; ++s) {
            float d_sub = d * (float)sc[s];
            float m_sub = dmin * (float)m[s];
            int qs_offset = (s / 2) * 32;
            int shift = (s % 2 == 0) ? 0 : 4;
            for (int l = 0; l < 32; ++l) {
                uint8_t ql = (qs[qs_offset + l] >> shift) & 0x0F;
                uint8_t h_bit = (qh[l] >> s) & 1;
                uint8_t q = ql | (h_bit << 4);
                float val = d_sub * (float)q - m_sub;
                b_sum += val * xs[s * 32 + l];
            }
        }
        total += b_sum;
    }
    return total;
}

static inline float dot_q6_K_row8192(const block_q6_K_t* row_blocks, const float* x) {
    float total = 0.0f;
    for (int sb = 0; sb < BLOCKS_PER_ROW_8192; ++sb) {
        const block_q6_K_t* b = &row_blocks[sb];
        float d = fp16_to_fp32(b->d);
        const uint8_t* ql = b->ql;
        const uint8_t* qh = b->qh;
        const int8_t*  sc = b->scales;
        const float* xs = x + sb * 256;
        float b_sum = 0.0f;
        for (int n = 0; n < 256; n += 128) {
            for (int l = 0; l < 32; ++l) {
                int is = l / 16;
                int8_t q1 = (int8_t)((ql[l +  0] & 0xF) | (((qh[l] >> 0) & 3) << 4)) - 32;
                int8_t q2 = (int8_t)((ql[l + 32] & 0xF) | (((qh[l] >> 2) & 3) << 4)) - 32;
                int8_t q3 = (int8_t)((ql[l +  0] >>  4) | (((qh[l] >> 4) & 3) << 4)) - 32;
                int8_t q4 = (int8_t)((ql[l + 32] >>  4) | (((qh[l] >> 6) & 3) << 4)) - 32;
                b_sum += d * (float)sc[is + 0] * (float)q1 * xs[n + l +  0];
                b_sum += d * (float)sc[is + 2] * (float)q2 * xs[n + l + 32];
                b_sum += d * (float)sc[is + 4] * (float)q3 * xs[n + l + 64];
                b_sum += d * (float)sc[is + 6] * (float)q4 * xs[n + l + 96];
            }
            ql += 64; qh += 32; sc += 8;
        }
        total += b_sum;
    }
    return total;
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
        q = (int8_t)((ql[l +  0] >>  4) | (((qh[l] >> 4) & 3) << 4)) - 32;
        scale = (float)sc[is + 4];
    } else {
        q = (int8_t)((ql[l + 32] >>  4) | (((qh[l] >> 6) & 3) << 4)) - 32;
        scale = (float)sc[is + 6];
    }
    return d * scale * (float)q;
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
} mt_task_70b_t;

static DWORD WINAPI worker_proc_70b(LPVOID param) {
    mt_task_70b_t* t = (mt_task_70b_t*)param;
    if (t->task_type == 1) { /* Q, K, V */
        for (int r = t->start_row; r < t->end_row; ++r) {
            t->out_a[r] = dot_q4_K_row8192((const block_q4_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_8192_Q4K), t->x_norm);
            if (r < DIM_KV) {
                t->out_b[r] = dot_q4_K_row8192((const block_q4_K_t*)(t->raw_b + (size_t)r * ROW_BYTES_8192_Q4K), t->x_norm);
                if (t->type_c == 14) {
                    t->out_c[r] = dot_q6_K_row8192((const block_q6_K_t*)(t->raw_c + (size_t)r * ROW_BYTES_8192_Q6K), t->x_norm);
                } else {
                    t->out_c[r] = dot_q5_K_row8192((const block_q5_K_t*)(t->raw_c + (size_t)r * ROW_BYTES_8192_Q5K), t->x_norm);
                }
            }
        }
    } else if (t->task_type == 2) { /* Wo (attn_output) */
        for (int r = t->start_row; r < t->end_row; ++r) {
            t->out_a[r] += dot_q4_K_row8192((const block_q4_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_8192_Q4K), t->x_norm);
        }
    } else if (t->task_type == 5) { /* Down Sparse (k_use colonnes) */
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
                const block_q6_K_t* head_row = (const block_q6_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_8192_Q6K);
                t->out_a[r] = dot_q6_K_row8192(head_row, t->x_norm);
            }
        } else {
            for (int r = t->start_row; r < t->end_row; ++r) {
                const block_q6_K_t* head_row = (const block_q6_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_8192_Q6K);
                t->out_a[r] = dot_q6_K_row8192(head_row, t->x_norm);
            }
        }
    } else if (t->task_type == 7) { /* Coarse Gate Screening (512 dims, 2 blocs) */
        for (int n = t->start_row; n < t->end_row; ++n) {
            const block_q4_K_t* g_row = (const block_q4_K_t*)(t->raw_a + (size_t)n * ROW_BYTES_8192_Q4K);
            t->out_a[n] = dot_q4_K_row512(g_row, t->x_norm);
        }
    } else if (t->task_type == 8) { /* Fine SwiGLU pour les k_use neurones ciblés */
        for (int i = t->start_row; i < t->end_row; ++i) {
            int n = t->neuron_list[i];
            const block_q4_K_t* g_row = (const block_q4_K_t*)(t->raw_a + (size_t)n * ROW_BYTES_8192_Q4K);
            const block_q4_K_t* u_row = (const block_q4_K_t*)(t->raw_b + (size_t)n * ROW_BYTES_8192_Q4K);
            float g = dot_q4_K_row8192(g_row, t->x_norm);
            float u = dot_q4_K_row8192(u_row, t->x_norm);
            float s = g / (1.0f + expf(-g));
            t->out_a[n] = s * u;
        }
    }
    return 0;
}

static void run_parallel_70b(int total_rows, int task_type, const float* x_norm,
                             const uint8_t* raw_a, const uint8_t* raw_b, const uint8_t* raw_c,
                             int type_c, float* out_a, float* out_b, float* out_c,
                             const int* neuron_list, int k_use, float alpha) {
    HANDLE threads[NUM_THREADS];
    mt_task_70b_t tasks[NUM_THREADS];
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
        threads[i] = CreateThread(NULL, 0, worker_proc_70b, &tasks[i], 0, NULL);
    }
    WaitForMultipleObjects(NUM_THREADS, threads, TRUE, INFINITE);
    for (int i = 0; i < NUM_THREADS; ++i) CloseHandle(threads[i]);
}

void alix_rmsnorm_70b(const float* x, const float* w_norm, float* out, int dim) {
    float sum_sq = 0.0f;
    for (int i = 0; i < dim; ++i) sum_sq += x[i] * x[i];
    float inv_rms = 1.0f / sqrtf((sum_sq / (float)dim) + EPS_RMSNORM);
    for (int i = 0; i < dim; ++i) out[i] = x[i] * inv_rms * w_norm[i];
}

void alix_apply_rope_70b(float* vec, int num_heads, int head_dim, int pos, float theta_base) {
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

void forward_one_layer_70b(
    alix_laser_file_t* file,
    int l,
    int pos,
    float* x,
    float* k_cache,
    float* v_cache,
    int k_use,
    int fovea_mode, /* 1 = Coarse-to-fine dynamique, 2 = Fovéa géométrique Christian */
    float* x_norm,
    float* q_vec,
    float* k_vec,
    float* v_vec,
    float* attn_o,
    float* h_act,
    int* top_idx
) {
    const alix_llama70b_full_layer_offsets_t* L = &LLAMA70B_FULL_OFFSETS[l];

    const float* w_anorm = (const float*)alix_laser_mmap_pointer(file, L->attn_norm_off);
    alix_rmsnorm_70b(x, w_anorm, x_norm, DIM_MODEL);

    const uint8_t* raw_q = (const uint8_t*)alix_laser_mmap_pointer(file, L->attn_q_off);
    const uint8_t* raw_k = (const uint8_t*)alix_laser_mmap_pointer(file, L->attn_k_off);
    const uint8_t* raw_v = (const uint8_t*)alix_laser_mmap_pointer(file, L->attn_v_off);

    run_parallel_70b(DIM_MODEL, 1, x_norm, raw_q, raw_k, raw_v, L->attn_v_type, q_vec, k_vec, v_vec, NULL, 0, 1.0f);

    alix_apply_rope_70b(q_vec, NUM_HEADS, HEAD_DIM, pos, ROPE_THETA);
    alix_apply_rope_70b(k_vec, NUM_KV_HEADS, HEAD_DIM, pos, ROPE_THETA);

    float* k_slot = k_cache + ((size_t)l * MAX_SEQ_LEN + pos) * DIM_KV;
    float* v_slot = v_cache + ((size_t)l * MAX_SEQ_LEN + pos) * DIM_KV;
    memcpy(k_slot, k_vec, DIM_KV * sizeof(float));
    memcpy(v_slot, v_vec, DIM_KV * sizeof(float));

    /* Attention GQA 64:8 */
    memset(attn_o, 0, DIM_MODEL * sizeof(float));
    float scores[MAX_SEQ_LEN];
    float scale = 1.0f / sqrtf((float)HEAD_DIM);

    for (int h = 0; h < NUM_HEADS; ++h) {
        int kv_h = h / GQA_GROUP;
        const float* q_h = q_vec + h * HEAD_DIM;
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
    run_parallel_70b(DIM_MODEL, 2, attn_o, raw_wo, NULL, NULL, 0, x, NULL, NULL, NULL, 0, 1.0f);

    const float* w_fnorm = (const float*)alix_laser_mmap_pointer(file, L->ffn_norm_off);
    alix_rmsnorm_70b(x, w_fnorm, x_norm, DIM_MODEL);

    const uint8_t* raw_gate = (const uint8_t*)alix_laser_mmap_pointer(file, L->ffn_gate_off);
    const uint8_t* raw_up   = (const uint8_t*)alix_laser_mmap_pointer(file, L->ffn_up_off);
    const uint8_t* raw_down = (const uint8_t*)alix_laser_mmap_pointer(file, L->ffn_down_off);

    if (fovea_mode == 1) {
        /* ====================================================================
         *   MODE 1 : CRIBLAGE COARSE-TO-FINE DYNAMIQUE SUR 4096 NEURONES
         * ==================================================================== */
        int coarse_pool = 4096; /* 4096 neurones primaires = 18.8 Mo sur USB au lieu de 264 Mo ! */
        run_parallel_70b(coarse_pool, 7, x_norm, raw_gate, NULL, NULL, 0, h_act, NULL, NULL, NULL, 0, 1.0f);

        /* Sélection des Top-K les plus chauds */
        float sum_sq_topk = 0.0f;
        for (int i = 0; i < k_use; ++i) {
            int best_j = -1;
            float best_v = -1.0f;
            for (int j = 0; j < coarse_pool; ++j) {
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

        /* SwiGLU fin 8192-dim UNIQUEMENT sur les k_use neurones gagnants */
        run_parallel_70b(k_use, 8, x_norm, raw_gate, raw_up, NULL, 0, h_act, NULL, NULL, top_idx, k_use, 1.0f);

        for (int i = 0; i < k_use; ++i) {
            sum_sq_topk += h_act[top_idx[i]] * h_act[top_idx[i]];
        }

        /* Down-projection sparse */
        float alpha = 1.8f;
        run_parallel_70b(DIM_MODEL, 5, h_act, raw_down, NULL, NULL, L->ffn_down_type, x, NULL, NULL, top_idx, k_use, alpha);

    } else {
        /* ====================================================================
         *   MODE 2 : FOVÉA GÉOMÉTRIQUE DE CHRISTIAN (80 NEURONES STATIQUES)
         * ==================================================================== */
        int fovea_k = 80;
        memcpy(top_idx, FOVEA_GEO_FRANCE_80, fovea_k * sizeof(int));

        /* SwiGLU fin 8192-dim uniquement sur les 80 neurones fovéaux (zéro scan !) */
        run_parallel_70b(fovea_k, 8, x_norm, raw_gate, raw_up, NULL, 0, h_act, NULL, NULL, top_idx, fovea_k, 1.0f);

        /* Down-projection avec Boost Fovéal de Christian */
        float alpha = 3.5f;
        run_parallel_70b(DIM_MODEL, 5, h_act, raw_down, NULL, NULL, L->ffn_down_type, x, NULL, NULL, top_idx, fovea_k, alpha);
    }
}

typedef struct {
    int best_token_id;
    float best_logit;
    char best_str[64];
    int top_ids[5];
    float top_lgs[5];
    char top_strs[5][64];
} step_result_70b_t;

int main(int argc, char** argv) {
    setvbuf(stdout, NULL, _IONBF, 0);
    SetConsoleOutputCP(CP_UTF8);

    int top_n = 5;
    bool json_output = false;
    bool prune_vocab = true;
    int steps_requested = 1;
    int domain_choice = 1; /* Défaut : France (Paris) */
    int fovea_mode = 1;    /* 1 = Coarse-to-fine dynamique, 2 = Fovéa géométrique Christian */
    int user_tokens[MAX_SEQ_LEN];
    int n_tokens = 0;
    int laser_focus_k = 500; /* Foyer Laser 500 neurones (ou 80 en mode 2) */
    int cutoff_layers = 40;  /* Test rapide : 40 couches de titan (ou 77 complet) */

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--json") == 0) {
            json_output = true;
        } else if (strcmp(argv[i], "--top") == 0 && i + 1 < argc) {
            top_n = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--k") == 0 && i + 1 < argc) {
            laser_focus_k = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--mode") == 0 && i + 1 < argc) {
            fovea_mode = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--cutoff") == 0 && i + 1 < argc) {
            cutoff_layers = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--domain") == 0 && i + 1 < argc) {
            domain_choice = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--steps") == 0 && i + 1 < argc) {
            steps_requested = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--dense-vocab") == 0) {
            prune_vocab = false;
        } else if (strcmp(argv[i], "--tokens") == 0 && i + 1 < argc) {
            char* tok_str = argv[++i];
            char* p = strtok(tok_str, ", ");
            while (p && n_tokens < MAX_SEQ_LEN) {
                user_tokens[n_tokens++] = atoi(p);
                p = strtok(NULL, ", ");
            }
        }
    }

    if (top_n <= 0 || top_n > 50) top_n = 5;
    if (laser_focus_k <= 0 || laser_focus_k > 4000) laser_focus_k = 500;
    if (cutoff_layers <= 5 || cutoff_layers > TOTAL_LAYERS) cutoff_layers = 40;
    if (steps_requested < 1) steps_requested = 1;
    if (steps_requested > 8) steps_requested = 8;

    int prompt_tokens[MAX_SEQ_LEN];
    int n_prompt = 0;
    const char* domain_title = "Personnalisé";

    if (n_tokens > 0) {
        n_prompt = n_tokens;
        memcpy(prompt_tokens, user_tokens, n_tokens * sizeof(int));
    } else {
        if (domain_choice == 1) {
            domain_title = "Géographie (France -> Paris)";
            int d1[] = {128000, 8921, 61510, 1604, 409, 1208, 9822, 1826, 551};
            n_prompt = sizeof(d1) / sizeof(d1[0]);
            memcpy(prompt_tokens, d1, sizeof(d1));
        } else if (domain_choice == 2) {
            domain_title = "Géographie Piège (Australie -> Canberra)";
            int d2[] = {128000, 8921, 61510, 1604, 409, 326, 52374, 5523, 648, 1826, 551};
            n_prompt = sizeof(d2) / sizeof(d2[0]);
            memcpy(prompt_tokens, d2, sizeof(d2));
        } else if (domain_choice == 3) {
            domain_title = "Chimie (Symbole Fe -> Fer)";
            int d3[] = {128000, 2356, 8045, 61175, 38094, 2428, 3926, 46838, 19388, 514, 551};
            n_prompt = sizeof(d3) / sizeof(d3[0]);
            memcpy(prompt_tokens, d3, sizeof(d3));
        } else {
            domain_title = "Mathématiques (7 x 8)";
            int d4[] = {128000, 2356, 1407, 266, 409, 325, 418, 86633, 71, 3159, 1826, 551};
            n_prompt = sizeof(d4) / sizeof(d4[0]);
            memcpy(prompt_tokens, d4, sizeof(d4));
        }
    }

    const wchar_t* usb_path = L"E:\\Modeles_4e_Etage\\Llama-3.3-70B-Instruct-Q4_K_M.gguf";
    const char* vocab_path = "C:\\Users\\Christian\\Documents\\Cerveau Alix\\_Unification_Alix\\src\\alix\\cortex_c99\\llama3_vocab.bin";

    alix_vocab_t vocab;
    if (!alix_vocab_load(&vocab, vocab_path)) {
        printf("Erreur de chargement du vocabulaire Llama-3 : %s\n", vocab_path);
        return 1;
    }

    /* Fovéa Lexicale Llama-3 (Mots-entités débutant par Ġ / \xc4\xa0) */
    int* fovea_tokens = (int*)malloc(VOCAB_SIZE * sizeof(int));
    int fovea_count = 0;
    if (prune_vocab) {
        for (int v = 0; v < VOCAB_SIZE; ++v) {
            char tbuf[64];
            alix_vocab_get_token(&vocab, v, tbuf, sizeof(tbuf));
            unsigned char c0 = (unsigned char)tbuf[0];
            unsigned char c1 = (unsigned char)tbuf[1];
            if (c0 == 0xC4 && c1 == 0xA0) {
                fovea_tokens[fovea_count++] = v;
            }
        }
    }

    alix_laser_file_t file;
    if (!alix_laser_open(&file, usb_path, ALIX_IO_MMAP)) {
        printf("Erreur : impossible d'ouvrir le titan 70B sur la clé USB : E:\\Modeles_4e_Etage\\Llama-3.3-70B-Instruct-Q4_K_M.gguf\n");
        return 1;
    }

    float* k_cache = (float*)calloc((size_t)TOTAL_LAYERS * MAX_SEQ_LEN * DIM_KV, sizeof(float));
    float* v_cache = (float*)calloc((size_t)TOTAL_LAYERS * MAX_SEQ_LEN * DIM_KV, sizeof(float));
    float* x       = (float*)malloc(DIM_MODEL * sizeof(float));
    float* x_norm  = (float*)malloc(DIM_MODEL * sizeof(float));
    float* q_vec   = (float*)malloc(DIM_MODEL * sizeof(float));
    float* k_vec   = (float*)malloc(DIM_KV * sizeof(float));
    float* v_vec   = (float*)malloc(DIM_KV * sizeof(float));
    float* attn_o  = (float*)malloc(DIM_MODEL * sizeof(float));
    float* h_act   = (float*)malloc(DIM_FFN * sizeof(float));
    int*   top_idx = (int*)malloc(DIM_FFN * sizeof(int));
    float* logits  = (float*)malloc(VOCAB_SIZE * sizeof(float));

    const uint8_t* raw_emb    = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_TOKEN_EMBD_OFFSET);
    const float*   w_out_norm = (const float*)alix_laser_mmap_pointer(&file, LLAMA70B_OUTPUT_NORM_OFFSET);
    const uint8_t* raw_out    = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_OUTPUT_OFFSET);

    /* Chargement ou calcul du cache KV */
    char kv_cache_file[512];
    snprintf(kv_cache_file, sizeof(kv_cache_file), "C:\\Users\\Christian\\Documents\\Cerveau Alix\\_Unification_Alix\\src\\alix\\cortex_c99\\llama70b_kv_domain%d.bin", domain_choice);
    size_t kv_bytes = (size_t)TOTAL_LAYERS * MAX_SEQ_LEN * DIM_KV * sizeof(float);
    FILE* fkv = fopen(kv_cache_file, "rb");
    bool loaded_kv = false;
    if (fkv && n_tokens == 0) {
        fread(k_cache, 1, kv_bytes, fkv);
        fread(v_cache, 1, kv_bytes, fkv);
        fclose(fkv);
        loaded_kv = true;
    }

    double t0 = get_time_ms();

    /* 1. Prefill des tokens de la question si pas encore en cache */
    if (!loaded_kv && n_prompt > 1) {
        if (!json_output) printf("  [Prefill 70B USB] Construction contexte %d tokens (L00..L%02d | Mode %d)...\n",
                                 n_prompt - 1, cutoff_layers - 1, fovea_mode);
        for (int pos = 0; pos < n_prompt - 1; ++pos) {
            int tid = prompt_tokens[pos];
            const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_emb + (size_t)tid * ROW_BYTES_8192_Q4K);
            for (int sb = 0; sb < BLOCKS_PER_ROW_8192; ++sb) {
                float d = fp16_to_fp32(emb_row[sb].d);
                float dmin = fp16_to_fp32(emb_row[sb].dmin);
                uint8_t sc[8], m[8];
                for (int j = 0; j < 4; ++j) {
                    sc[j]     = emb_row[sb].scales[j] & 63;
                    m[j]      = emb_row[sb].scales[j + 4] & 63;
                    sc[j + 4] = (emb_row[sb].scales[j + 8] & 15) | ((emb_row[sb].scales[j] >> 6) << 4);
                    m[j + 4]  = (emb_row[sb].scales[j + 8] >> 4) | ((emb_row[sb].scales[j + 4] >> 6) << 4);
                }
                const uint8_t* q = emb_row[sb].qs;
                for (int j = 0; j < 4; ++j) {
                    float d1 = d * (float)sc[2 * j];
                    float m1 = dmin * (float)m[2 * j];
                    float d2 = d * (float)sc[2 * j + 1];
                    float m2 = dmin * (float)m[2 * j + 1];
                    for (int l = 0; l < 32; ++l) {
                        uint8_t byte_val = q[j * 32 + l];
                        x[sb * 256 + j * 64 + l]      = d1 * (float)(byte_val & 0x0F) - m1;
                        x[sb * 256 + j * 64 + 32 + l] = d2 * (float)(byte_val >> 4)   - m2;
                    }
                }
            }
            for (int l = 0; l < cutoff_layers; ++l) {
                forward_one_layer_70b(&file, l, pos, x, k_cache, v_cache, (fovea_mode == 2 ? 80 : 200), fovea_mode,
                                      x_norm, q_vec, k_vec, v_vec, attn_o, h_act, top_idx);
            }
        }
        if (n_tokens == 0) {
            fkv = fopen(kv_cache_file, "wb");
            if (fkv) {
                fwrite(k_cache, 1, kv_bytes, fkv);
                fwrite(v_cache, 1, kv_bytes, fkv);
                fclose(fkv);
            }
        }
    }

    /* 2. Tir Transversal Landauer sur Titan 70B */
    step_result_70b_t results[8];
    int actual_steps = 0;
    double t_layers_cumul = 0.0;
    double t_lmhead_cumul = 0.0;
    char phrase_buf[512] = "";

    for (int step = 0; step < steps_requested; ++step) {
        int pos = (n_prompt - 1) + step;
        int tid = prompt_tokens[pos];

        const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_emb + (size_t)tid * ROW_BYTES_8192_Q4K);
        for (int sb = 0; sb < BLOCKS_PER_ROW_8192; ++sb) {
            float d = fp16_to_fp32(emb_row[sb].d);
            float dmin = fp16_to_fp32(emb_row[sb].dmin);
            uint8_t sc[8], m[8];
            for (int j = 0; j < 4; ++j) {
                sc[j]     = emb_row[sb].scales[j] & 63;
                m[j]      = emb_row[sb].scales[j + 4] & 63;
                sc[j + 4] = (emb_row[sb].scales[j + 8] & 15) | ((emb_row[sb].scales[j] >> 6) << 4);
                m[j + 4]  = (emb_row[sb].scales[j + 8] >> 4) | ((emb_row[sb].scales[j + 4] >> 6) << 4);
            }
            const uint8_t* q = emb_row[sb].qs;
            for (int j = 0; j < 4; ++j) {
                float d1 = d * (float)sc[2 * j];
                float m1 = dmin * (float)m[2 * j];
                float d2 = d * (float)sc[2 * j + 1];
                float m2 = dmin * (float)m[2 * j + 1];
                for (int l = 0; l < 32; ++l) {
                    uint8_t byte_val = q[j * 32 + l];
                    x[sb * 256 + j * 64 + l]      = d1 * (float)(byte_val & 0x0F) - m1;
                    x[sb * 256 + j * 64 + 32 + l] = d2 * (float)(byte_val >> 4)   - m2;
                }
            }
        }

        double tl0 = get_time_ms();
        for (int l = 0; l < cutoff_layers; ++l) {
            int k_layer = laser_focus_k;
            if (fovea_mode == 2) k_layer = 80;
            forward_one_layer_70b(&file, l, pos, x, k_cache, v_cache, k_layer, fovea_mode,
                                  x_norm, q_vec, k_vec, v_vec, attn_o, h_act, top_idx);
        }
        t_layers_cumul += (get_time_ms() - tl0);

        /* Logit Lens direct à la sortie de L(cutoff-1) */
        alix_rmsnorm_70b(x, w_out_norm, x_norm, DIM_MODEL);

        for (int v = 0; v < VOCAB_SIZE; ++v) logits[v] = -1e30f;

        double th0 = get_time_ms();
        if (prune_vocab && fovea_count > 0) {
            run_parallel_70b(fovea_count, 6, x_norm, raw_out, NULL, NULL, 14, logits, NULL, NULL, fovea_tokens, 0, 1.0f);
        } else {
            run_parallel_70b(VOCAB_SIZE, 6, x_norm, raw_out, NULL, NULL, 14, logits, NULL, NULL, NULL, 0, 1.0f);
        }
        t_lmhead_cumul += (get_time_ms() - th0);

        /* Extraction des Top-N */
        int step_top_ids[50];
        float step_top_lgs[50];
        for (int i = 0; i < top_n; ++i) {
            step_top_ids[i] = -1;
            step_top_lgs[i] = -1e30f;
        }

        int scan_count = (prune_vocab && fovea_count > 0) ? fovea_count : VOCAB_SIZE;
        for (int idx = 0; idx < scan_count; ++idx) {
            int v = (prune_vocab && fovea_count > 0) ? fovea_tokens[idx] : idx;
            float lg = logits[v];
            for (int i = 0; i < top_n; ++i) {
                if (lg > step_top_lgs[i]) {
                    for (int m = top_n - 1; m > i; --m) {
                        step_top_lgs[m] = step_top_lgs[m - 1];
                        step_top_ids[m] = step_top_ids[m - 1];
                    }
                    step_top_lgs[i] = lg;
                    step_top_ids[i] = v;
                    break;
                }
            }
        }

        step_result_70b_t* sr = &results[step];
        sr->best_token_id = step_top_ids[0];
        sr->best_logit = step_top_lgs[0];
        alix_vocab_get_token(&vocab, sr->best_token_id, sr->best_str, sizeof(sr->best_str));
        strncat(phrase_buf, sr->best_str, sizeof(phrase_buf) - strlen(phrase_buf) - 1);

        for (int i = 0; i < top_n && i < 5; ++i) {
            sr->top_ids[i] = step_top_ids[i];
            sr->top_lgs[i] = step_top_lgs[i];
            alix_vocab_get_token(&vocab, step_top_ids[i], sr->top_strs[i], sizeof(sr->top_strs[i]));
        }

        prompt_tokens[pos + 1] = sr->best_token_id;
        actual_steps++;

        if (sr->best_token_id == 128001 || sr->best_token_id == 128009) break;
    }

    double total_elapsed_ms = get_time_ms() - t0;

    if (json_output) {
        printf("{\n");
        printf("  \"status\": \"ok\",\n");
        printf("  \"model\": \"Llama-3.3-70B-Instruct-Q4_K_M\",\n");
        printf("  \"domain\": \"%s\",\n", domain_title);
        printf("  \"mode\": %d,\n", fovea_mode);
        printf("  \"laser_k\": %d,\n", (fovea_mode == 2 ? 80 : laser_focus_k));
        printf("  \"layers_traversed\": %d,\n", cutoff_layers);
        printf("  \"prune_vocab\": %s,\n", prune_vocab ? "true" : "false");
        printf("  \"fovea_tokens\": %d,\n", fovea_count);
        printf("  \"steps\": %d,\n", actual_steps);
        printf("  \"phrase\": \"%s\",\n", phrase_buf);
        printf("  \"timings\": {\n");
        printf("    \"layers_ms\": %.2f,\n", t_layers_cumul);
        printf("    \"lmhead_ms\": %.2f,\n", t_lmhead_cumul);
        printf("    \"total_ms\": %.2f\n", total_elapsed_ms);
        printf("  },\n");
        printf("  \"step_results\": [\n");
        for (int s = 0; s < actual_steps; ++s) {
            step_result_70b_t* sr = &results[s];
            printf("    {\n");
            printf("      \"step\": %d,\n", s + 1);
            printf("      \"token_id\": %d,\n", sr->best_token_id);
            printf("      \"token_str\": \"%s\",\n", sr->best_str);
            printf("      \"logit\": %.4f,\n", sr->best_logit);
            printf("      \"semantic_links\": [\n");
            for (int i = 0; i < top_n && i < 5; ++i) {
                printf("        {\"token_id\": %d, \"str\": \"%s\", \"logit\": %.4f}%s\n",
                       sr->top_ids[i], sr->top_strs[i], sr->top_lgs[i], (i + 1 < top_n && i + 1 < 5) ? "," : "");
            }
            printf("      ]\n");
            printf("    }%s\n", (s + 1 < actual_steps) ? "," : "");
        }
        printf("  ]\n");
        printf("}\n");
    } else {
        printf("==============================================================================\n");
        printf("  🏛️⚡ SONDE LANDAUER SUR TITAN 70B (MODE %d | SORTIE L%02d)\n",
               fovea_mode, cutoff_layers - 1);
        printf("==============================================================================\n");
        printf("  • Modèle Cible    : Llama-3.3-70B-Instruct (42.5 Go sur Clé USB E:\\)\n");
        printf("  • Domaine / Cible : %s\n", domain_title);
        printf("  • Stratégie Fovéa : %s\n", (fovea_mode == 1 ? "Option 1 (Criblage Coarse-to-Fine 512-dim)" : "Option 2 (Fovéa Géométrique Christian 80n)"));
        printf("  • Foyer Laser     : %d neurones (sur 28672 MLP - %.2f %%)\n",
               (fovea_mode == 2 ? 80 : laser_focus_k),
               (double)(fovea_mode == 2 ? 80 : laser_focus_k) * 100.0 / (double)DIM_FFN);
        printf("  • Vocabulaire Ġ   : %d tokens de mots évalués (sur 128256)\n", fovea_count);
        printf("  • Strates lues    : Couches L00 à L%02d (%d couches sur 80 — L%02d..L79 zappées)\n",
               cutoff_layers - 1, cutoff_layers, cutoff_layers);
        printf("  • Chronométrage   : Total %.2f ms (%.2f s) [KV Cache: %s]\n",
               total_elapsed_ms, total_elapsed_ms / 1000.0, loaded_kv ? "ACTIF EN RAM/DISK" : "CALCULÉ");
        printf("    └─ Couches L00..L%02d : %.2f ms (%.2f ms / couche)\n",
               cutoff_layers - 1, t_layers_cumul, t_layers_cumul / (double)cutoff_layers);
        printf("    └─ Projection LM_Head : %.2f ms\n", t_lmhead_cumul);
        printf("------------------------------------------------------------------------------\n");
        if (actual_steps > 1) {
            printf("  💬 PHRASE EXTRAITE DU TITAN 70B : \"%s\"\n", phrase_buf);
            printf("------------------------------------------------------------------------------\n");
            printf("  🔗 LIENS SÉMANTIQUES ENTRE CONCEPTS (PAR ÉTAPE) :\n");
            for (int s = 0; s < actual_steps; ++s) {
                step_result_70b_t* sr = &results[s];
                printf("    [Étape %d : '%s'] Résonances -> ", s + 1, sr->best_str);
                for (int i = 0; i < top_n && i < 5; ++i) {
                    printf("'%s' (%.1f)%s", sr->top_strs[i], sr->top_lgs[i], (i + 1 < top_n && i + 1 < 5) ? ", " : "");
                }
                printf("\n");
            }
        } else {
            printf("  🎯 FAITS PURS & LIENS SÉMANTIQUES (SORTIE L%02d SUR 70B) :\n", cutoff_layers - 1);
            step_result_70b_t* sr = &results[0];
            for (int i = 0; i < top_n && i < 5; ++i) {
                printf("    #%d [%-6d] '%s' (logit: %.2f)\n", i + 1, sr->top_ids[i], sr->top_strs[i], sr->top_lgs[i]);
            }
        }
        printf("==============================================================================\n");
    }

    alix_laser_close(&file);
    free(fovea_tokens);
    free(k_cache); free(v_cache); free(x); free(x_norm);
    free(q_vec); free(k_vec); free(v_vec); free(attn_o); free(h_act); free(top_idx); free(logits);
    return 0;
}
