/**
 * ============================================================================
 *   🏛️⚡ ALIX SCALPEL LANDAUER : LA SONDE TRANSVERSALE À 500 NEURONES
 *   Fichier : alix_scalpel_landauer.c (C99 Win32 / Intel Lunar Lake AVX2)
 * ============================================================================
 *   Doctrine :
 *     - Faisceau Laser : 500 neurones sur le canal actif (L08..L28).
 *     - Traversée transversale : traque l'invariant d'information minimale (Landauer).
 *     - Coupure nette à la Couche 28 : arrêt avant les 3 couches cosmétiques (L29..L31).
 *     - Décodage Logit Lens direct sur la strate 28.
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
#define CUTOFF_LAYERS       29    /* Arrêt net à L28 (0..28) : on zappe L29, L30, L31 ! */
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
        uint32_t res = sign | 0x7F800000 | (mant << 13);
        float f; memcpy(&f, &res, 4); return f;
    }
    exp = exp + (127 - 15);
    uint32_t res = sign | (exp << 23) | (mant << 13);
    float f; memcpy(&f, &res, 4); return f;
}

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
        q = (int8_t)((ql[l +  0] >>  4) | (((qh[l] >> 4) & 3) << 4)) - 32;
        scale = (float)sc[is + 4];
    } else {
        q = (int8_t)((ql[l + 32] >>  4) | (((qh[l] >> 6) & 3) << 4)) - 32;
        scale = (float)sc[is + 6];
    }
    return d * scale * (float)q;
}

static inline float dot_q4_K_row4096(const block_q4_K_t* row_blocks, const float* x) {
    float total = 0.0f;
    for (int sb = 0; sb < BLOCKS_PER_ROW_4096; ++sb) {
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

static inline float dot_q6_K_row4096(const block_q6_K_t* row_blocks, const float* x) {
    float total = 0.0f;
    for (int sb = 0; sb < BLOCKS_PER_ROW_4096; ++sb) {
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
    } else if (t->task_type == 5) { /* Down Sparse (K colonnes ciblées) */
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
    } else if (t->task_type == 6) { /* lm_head (dense ou fovéa) */
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

    /* Calcul résonant SwiGLU */
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

        /* Conservation d'énergie Landauer (sqrt(alpha)) */
        float raw_alpha = (sum_sq_topk > 1e-12f) ? sqrtf(sum_sq_all / sum_sq_topk) : 1.0f;
        float alpha = (rescale_energy == 1) ? raw_alpha : ((rescale_energy == 2) ? sqrtf(raw_alpha) : 1.0f);

        run_parallel_ex(DIM_MODEL, 5, h_act, raw_down, NULL, NULL, L->ffn_down_type, x, NULL, NULL, top_idx, k_use, alpha);
    } else {
        run_parallel_ex(DIM_MODEL, 4, h_act, raw_down, NULL, NULL, L->ffn_down_type, x, NULL, NULL, NULL, 0, 1.0f);
    }
}

typedef struct {
    int best_token_id;
    float best_logit;
    char best_str[64];
    int top_ids[5];
    float top_lgs[5];
    char top_strs[5][64];
} step_result_t;

int main(int argc, char** argv) {
    SetConsoleOutputCP(CP_UTF8);

    int top_n = 5;
    bool json_output = false;
    bool prune_vocab = false;
    int steps_requested = 1;
    int domain_choice = 3; /* Défaut : Chimie (Fe -> Fer) */
    int user_tokens[MAX_SEQ_LEN];
    int n_tokens = 0;
    int laser_focus_k = 1000; /* Foyer Laser 1000 neurones (Noyau factuel L08..L28) */

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--json") == 0) {
            json_output = true;
        } else if (strcmp(argv[i], "--top") == 0 && i + 1 < argc) {
            top_n = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--k") == 0 && i + 1 < argc) {
            laser_focus_k = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--domain") == 0 && i + 1 < argc) {
            domain_choice = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--steps") == 0 && i + 1 < argc) {
            steps_requested = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--prune-vocab") == 0) {
            prune_vocab = true;
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
    if (laser_focus_k <= 0 || laser_focus_k > 2000) laser_focus_k = 1000;
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
            int d1[] = {32006, 1792, 13, 751, 1808, 707, 425, 27073, 316, 425, 3444, 1577, 32005, 13, 32006, 465, 22137, 13, 997, 27073, 316, 425, 3444, 707};
            n_prompt = sizeof(d1) / sizeof(d1[0]);
            memcpy(prompt_tokens, d1, sizeof(d1));
        } else if (domain_choice == 2) {
            domain_title = "Géographie Piège (Australie -> Canberra)";
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
    }

    const wchar_t* gguf_path = L"C:\\Users\\Christian\\.ollama\\models\\blobs\\sha256-07264f5b41a074562c3fd8bff0e1b7f60ecb4f3441ed5410db35529ee7a207ce";
    const char* vocab_path = "C:\\Users\\Christian\\Documents\\Cerveau Alix\\_Unification_Alix\\src\\alix\\cortex_c99\\tower7b_vocab.bin";

    alix_vocab_t vocab;
    if (!alix_vocab_load(&vocab, vocab_path)) return 1;

    /* Construction de la table de Fovéa Lexicale (Mots pleins / entités sémantiques) */
    int* fovea_tokens = (int*)malloc(VOCAB_SIZE * sizeof(int));
    int fovea_count = 0;
    if (prune_vocab) {
        for (int v = 0; v < VOCAB_SIZE; ++v) {
            if (is_parasitic_token(&vocab, v)) continue;
            char tbuf[64];
            alix_vocab_get_token(&vocab, v, tbuf, sizeof(tbuf));
            int blen = (int)strlen(tbuf);
            if (blen < 2) continue;
            unsigned char c0 = (unsigned char)tbuf[0];
            unsigned char c1 = (unsigned char)tbuf[1];
            bool is_word = false;
            if (c0 == ' ' || (c0 == 0xE2 && c1 == 0x96)) {
                is_word = true;
            } else if ((c0 >= 'a' && c0 <= 'z') || (c0 >= 'A' && c0 <= 'Z') || (c0 >= 0xC0)) {
                is_word = true;
            }
            if (is_word) {
                fovea_tokens[fovea_count++] = v;
            }
        }
    }

    alix_laser_file_t file;
    if (!alix_laser_open(&file, gguf_path, ALIX_IO_MMAP)) return 1;

    float* k_cache = (float*)calloc((size_t)TOTAL_LAYERS * MAX_SEQ_LEN * DIM_KV, sizeof(float));
    float* v_cache = (float*)calloc((size_t)TOTAL_LAYERS * MAX_SEQ_LEN * DIM_KV, sizeof(float));
    float* x       = (float*)malloc(DIM_MODEL * sizeof(float));
    float* x_norm  = (float*)malloc(DIM_MODEL * sizeof(float));
    float* q_vec   = (float*)malloc(DIM_MODEL * sizeof(float));
    float* attn_o  = (float*)malloc(DIM_MODEL * sizeof(float));
    float* h_act   = (float*)malloc(DIM_FFN * sizeof(float));
    int*   top_idx = (int*)malloc(DIM_FFN * sizeof(int));
    float* logits  = (float*)malloc(VOCAB_SIZE * sizeof(float));

    const uint8_t* raw_emb    = (const uint8_t*)alix_laser_mmap_pointer(&file, TOWER7B_TOKEN_EMBD_OFF);
    const float*   w_out_norm = (const float*)alix_laser_mmap_pointer(&file, TOWER7B_OUTPUT_NORM_OFF);
    const uint8_t* raw_out    = (const uint8_t*)alix_laser_mmap_pointer(&file, TOWER7B_OUTPUT_OFF);

    /* Chargement ou calcul du cache KV */
    char kv_cache_file[512];
    snprintf(kv_cache_file, sizeof(kv_cache_file), "C:\\Users\\Christian\\Documents\\Cerveau Alix\\_Unification_Alix\\src\\alix\\cortex_c99\\tower7b_kv_domain%d.bin", domain_choice);
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
        if (!json_output) printf("  [Prefill Landauer] Construction du contexte sur %d tokens (L00..L%02d)...\n",
                                 n_prompt - 1, CUTOFF_LAYERS - 1);
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
        if (n_tokens == 0) {
            fkv = fopen(kv_cache_file, "wb");
            if (fkv) {
                fwrite(k_cache, 1, kv_bytes, fkv);
                fwrite(v_cache, 1, kv_bytes, fkv);
                fclose(fkv);
            }
        }
    }

    /* 2. Tir Transversal Landauer (Génération multi-pas si demandée) */
    step_result_t results[8];
    int actual_steps = 0;
    double t_layers_cumul = 0.0;
    double t_lmhead_cumul = 0.0;
    char phrase_buf[512] = "";

    for (int step = 0; step < steps_requested; ++step) {
        int pos = (n_prompt - 1) + step;
        int tid = prompt_tokens[pos];

        const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_emb + (size_t)tid * ROW_BYTES_4096_Q4K);
        for (int sb = 0; sb < BLOCKS_PER_ROW_4096; ++sb) {
            dequantize_q4_K_block(&emb_row[sb], x + sb * 256);
        }

        double tl0 = get_time_ms();
        /* Traversée transversale jusqu'à la Couche 28 (Coupure nette des 3 couches cosmétiques !) */
        for (int l = 0; l < CUTOFF_LAYERS; ++l) {
            int k_layer = laser_focus_k;
            int resc = 2; /* sqrt(alpha) */
            if (l < 8) k_layer = 160; /* Entrée plus légère */
            forward_one_layer_landauer(&file, l, pos, x, k_cache, v_cache, k_layer, resc, x_norm, q_vec, attn_o, h_act, top_idx);
        }
        t_layers_cumul += (get_time_ms() - tl0);

        /* Logit Lens direct à la sortie de L28 (sans les couches cosmétiques L29..L31) */
        alix_rmsnorm(x, w_out_norm, x_norm, DIM_MODEL);

        /* Dump de l'état résiduel géométrique exact pour analyse topologique KAIROS */
        if (step == 0) {
            char dump_name[256];
            snprintf(dump_name, sizeof(dump_name), "C:\\Users\\Christian\\Documents\\Cerveau Alix\\_Unification_Alix\\src\\alix\\cortex_c99\\dump_xnorm_domain%d.bin", domain_choice);
            FILE* fdump = fopen(dump_name, "wb");
            if (fdump) {
                fwrite(x_norm, sizeof(float), DIM_MODEL, fdump);
                fclose(fdump);
            }
        }

        for (int v = 0; v < VOCAB_SIZE; ++v) logits[v] = -1e30f;

        double th0 = get_time_ms();
        if (prune_vocab && fovea_count > 0) {
            run_parallel_ex(fovea_count, 6, x_norm, raw_out, NULL, NULL, 14, logits, NULL, NULL, fovea_tokens, 0, 1.0f);
        } else {
            run_parallel_ex(VOCAB_SIZE, 6, x_norm, raw_out, NULL, NULL, 14, logits, NULL, NULL, NULL, 0, 1.0f);
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
            if (!prune_vocab && is_parasitic_token(&vocab, v)) continue;
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

        step_result_t* sr = &results[step];
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

        /* Arrêt si fin de phrase ou token spécial */
        if (sr->best_token_id == 2 || sr->best_token_id == 13 || sr->best_token_id == 32005) {
            break;
        }
    }

    double total_elapsed_ms = get_time_ms() - t0;

    if (json_output) {
        printf("{\n");
        printf("  \"status\": \"ok\",\n");
        printf("  \"domain\": \"%s\",\n", domain_title);
        printf("  \"laser_k\": %d,\n", laser_focus_k);
        printf("  \"layers_traversed\": %d,\n", CUTOFF_LAYERS);
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
            step_result_t* sr = &results[s];
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
        printf("  🏛️⚡ SONDE LANDAUER NEURONALE (FOCUS %d NEURONES | SORTIE L28)\n", laser_focus_k);
        printf("==============================================================================\n");
        printf("  • Domaine / Cible : %s\n", domain_title);
        printf("  • Foyer Laser     : %d neurones (Canal Landauer L08..L28)\n", laser_focus_k);
        printf("  • Mode Vocabulaire: %s (%d tokens évalués)\n",
               prune_vocab ? "Fovéa Sémantique (Élagué)" : "Dense (Complet)",
               prune_vocab ? fovea_count : VOCAB_SIZE);
        printf("  • Strates lues    : Couches L00 à L%02d (%d couches sur 32 — L29..L31 zappées)\n",
               CUTOFF_LAYERS - 1, CUTOFF_LAYERS);
        printf("  • Chronométrage   : Total %.2f ms (%.2f s) [KV Cache: %s]\n",
               total_elapsed_ms, total_elapsed_ms / 1000.0, loaded_kv ? "ACTIF EN RAM/DISK" : "CALCULÉ");
        printf("    └─ Couches L00..L28 : %.2f ms\n", t_layers_cumul);
        printf("    └─ Projection LM_Head: %.2f ms\n", t_lmhead_cumul);
        printf("------------------------------------------------------------------------------\n");
        if (actual_steps > 1) {
            printf("  💬 PHRASE EXTRAITE DU MODÈLE : \"%s\"\n", phrase_buf);
            printf("------------------------------------------------------------------------------\n");
            printf("  🔗 LIENS SÉMANTIQUES ENTRE CONCEPTS (PAR ÉTAPE) :\n");
            for (int s = 0; s < actual_steps; ++s) {
                step_result_t* sr = &results[s];
                printf("    [Étape %d : '%s'] Résonances -> ", s + 1, sr->best_str);
                for (int i = 0; i < top_n && i < 5; ++i) {
                    printf("'%s' (%.1f)%s", sr->top_strs[i], sr->top_lgs[i], (i + 1 < top_n && i + 1 < 5) ? ", " : "");
                }
                printf("\n");
            }
        } else {
            printf("  🎯 FAITS PURS & LIENS SÉMANTIQUES (SORTIE L28) :\n");
            step_result_t* sr = &results[0];
            for (int i = 0; i < top_n && i < 5; ++i) {
                printf("    #%d [%-6d] '%s' (logit: %.2f)\n", i + 1, sr->top_ids[i], sr->top_strs[i], sr->top_lgs[i]);
            }
        }
        printf("==============================================================================\n");
    }

    alix_laser_close(&file);
    free(fovea_tokens);
    free(k_cache); free(v_cache); free(x); free(x_norm);
    free(q_vec); free(attn_o); free(h_act); free(top_idx); free(logits);
    return 0;
}
