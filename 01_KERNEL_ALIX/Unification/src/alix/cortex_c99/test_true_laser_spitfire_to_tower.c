/**
 * ============================================================================
 *   🏛️⚡ C-ALIX : VRAIE LECTURE CHIRURGICALE (GATE + UP + DOWN COUPÉS)
 *   Fichier : test_true_laser_spitfire_to_tower.c
 * ============================================================================
 *   Répond au défi fondamental du 4e Étage :
 *   Au lieu de calculer les 11 008 neurones de `gate_proj` et `up_proj` (mode
 *   "oracle"), C-Alix utilise directement la table d'interrupteurs extraite
 *   de son jumeau Spitfire (`alix_spitfire_fovea.h`, `SPITFIRE_TOP_NEURONS`).
 *
 *   Pour chaque couche l et pour K neurones choisis AVANT lecture :
 *     - On ne lit et déquantifie QUE K lignes de `ffn_gate` (sur 11 008) !
 *     - On ne lit et déquantifie QUE K lignes de `ffn_up`   (sur 11 008) !
 *     - On ne calcule QUE les K colonnes correspondantes dans `ffn_down` !
 *
 *   Gain théorique et physique sur le FFN (qui pèse 67% du modèle) :
 *     - K = 80  -> 99.3% du FFN n'est JAMAIS LU ni calculé !
 *     - K = 250 -> 97.7% du FFN n'est JAMAIS LU ni calculé !
 * ============================================================================
 */

#include "alix_laser_io.h"
#include "alix_tower7b_full_offsets.h"
#include "alix_spitfire_fovea.h"
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
    float sum = 0.0f;
    float buf[256];
    for (int sb = 0; sb < BLOCKS_PER_ROW_4096; ++sb) {
        dequantize_q4_K_block(&row_blocks[sb], buf);
        const float* xs = x + sb * 256;
        for (int i = 0; i < 256; ++i) sum += buf[i] * xs[i];
    }
    return sum;
}

static inline float dot_q6_K_row4096(const block_q6_K_t* row_blocks, const float* x) {
    float sum = 0.0f;
    float buf[256];
    for (int sb = 0; sb < BLOCKS_PER_ROW_4096; ++sb) {
        dequantize_q6_K_block(&row_blocks[sb], buf);
        const float* xs = x + sb * 256;
        for (int i = 0; i < 256; ++i) sum += buf[i] * xs[i];
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
    const uint16_t* neuron_list;
    int k_use;
    float alpha;
} mt_task_t;

static DWORD WINAPI worker_proc(LPVOID param) {
    mt_task_t* t = (mt_task_t*)param;
    if (t->task_type == 1) { /* Q, K, V */
        for (int r = t->start_row; r < t->end_row; ++r) {
            const block_q4_K_t* q_row = (const block_q4_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_4096_Q4K);
            const block_q4_K_t* k_row = (const block_q4_K_t*)(t->raw_b + (size_t)r * ROW_BYTES_4096_Q4K);
            t->out_a[r] = dot_q4_K_row4096(q_row, t->x_norm);
            t->out_b[r] = dot_q4_K_row4096(k_row, t->x_norm);
            if (t->type_c == 14) {
                const block_q6_K_t* v_row = (const block_q6_K_t*)(t->raw_c + (size_t)r * ROW_BYTES_4096_Q6K);
                t->out_c[r] = dot_q6_K_row4096(v_row, t->x_norm);
            } else {
                const block_q4_K_t* v_row = (const block_q4_K_t*)(t->raw_c + (size_t)r * ROW_BYTES_4096_Q4K);
                t->out_c[r] = dot_q4_K_row4096(v_row, t->x_norm);
            }
        }
    } else if (t->task_type == 2) { /* Wo */
        for (int r = t->start_row; r < t->end_row; ++r) {
            const block_q4_K_t* wo_row = (const block_q4_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_4096_Q4K);
            t->out_a[r] += dot_q4_K_row4096(wo_row, t->x_norm);
        }
    } else if (t->task_type == 5) { /* Down Sparse (ne lit que les K colonnes de neuron_list !) */
        for (int r = t->start_row; r < t->end_row; ++r) {
            float sum_d = 0.0f;
            if (t->type_c == 14) {
                const block_q6_K_t* d_row = (const block_q6_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_DOWN_Q6K);
                for (int i = 0; i < t->k_use; ++i) {
                    int n_id = t->neuron_list[i];
                    sum_d += t->x_norm[i] * dequantize_q6_K_single(&d_row[n_id / 256], n_id % 256);
                }
            } else {
                const block_q4_K_t* d_row = (const block_q4_K_t*)(t->raw_a + (size_t)r * ROW_BYTES_DOWN_Q4K);
                for (int i = 0; i < t->k_use; ++i) {
                    int n_id = t->neuron_list[i];
                    sum_d += t->x_norm[i] * dequantize_q4_K_single(&d_row[n_id / 256], n_id % 256);
                }
            }
            t->out_a[r] += sum_d * t->alpha;
        }
    }
    return 0;
}

static void run_parallel_ex(int total_rows, int task_type, const float* x_norm,
                            const uint8_t* raw_a, const uint8_t* raw_b, const uint8_t* raw_c,
                            int type_c, float* out_a, float* out_b, float* out_c,
                            const uint16_t* neuron_list, int k_use, float alpha) {
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

/* ============================================================================
 * VRAI PASSAGE LASER C-ALIX : NE LIT QUE K NEURONES DANS GATE, UP ET DOWN !
 * ============================================================================ */
void forward_one_layer_true_laser(
    alix_laser_file_t* file,
    int l,
    int pos,
    float* x,
    float* k_cache,
    float* v_cache,
    int k_use,
    float alpha,
    float* x_norm,
    float* q_vec,
    float* attn_o,
    float* h_sparse,
    uint64_t* ffn_bytes_read
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

    /* ========================================================================
     * FFN LASER PUR : ON NE LIT QUE LES K NEURONES DE SPITFIRE_TOP_NEURONS[l] !
     * ======================================================================== */
    const float* w_fnorm = (const float*)alix_laser_mmap_pointer(file, L->ffn_norm_off);
    alix_rmsnorm(x, w_fnorm, x_norm, DIM_MODEL);

    const uint8_t* raw_gate = (const uint8_t*)alix_laser_mmap_pointer(file, L->ffn_gate_off);
    const uint8_t* raw_up   = (const uint8_t*)alix_laser_mmap_pointer(file, L->ffn_up_off);
    const uint8_t* raw_down = (const uint8_t*)alix_laser_mmap_pointer(file, L->ffn_down_off);

    const uint16_t* n_list = SPITFIRE_TOP_NEURONS[l];

    /* 1. Ne lire et calculer QUE les K lignes de Gate et Up ! */
    for (int i = 0; i < k_use; ++i) {
        int n_id = n_list[i];
        const block_q4_K_t* g_row = (const block_q4_K_t*)(raw_gate + (size_t)n_id * ROW_BYTES_4096_Q4K);
        const block_q4_K_t* u_row = (const block_q4_K_t*)(raw_up   + (size_t)n_id * ROW_BYTES_4096_Q4K);
        float g = dot_q4_K_row4096(g_row, x_norm);
        float u = dot_q4_K_row4096(u_row, x_norm);
        float silu_g = g / (1.0f + expf(-g));
        h_sparse[i] = silu_g * u;
    }

    /* 2. Ne calculer QUE les K colonnes dans Down (en parallèle sur 8 cœurs) ! */
    run_parallel_ex(DIM_MODEL, 5, h_sparse, raw_down, NULL, NULL, L->ffn_down_type, x, NULL, NULL, n_list, k_use, alpha);

    /* Comptabiliser les octets FFN réellement lus */
    uint64_t bytes_gate_up = (uint64_t)k_use * 2ULL * ROW_BYTES_4096_Q4K;
    uint64_t bytes_down    = (uint64_t)k_use * DIM_MODEL * sizeof(uint8_t); /* ~1 octet effectif par poids lu */
    *ffn_bytes_read += (bytes_gate_up + bytes_down);
}

int main(void) {
    SetConsoleOutputCP(CP_UTF8);
    const wchar_t* gguf_path = L"C:\\Users\\Christian\\.ollama\\models\\blobs\\sha256-07264f5b41a074562c3fd8bff0e1b7f60ecb4f3441ed5410db35529ee7a207ce";
    const char* vocab_path = "C:\\Users\\Christian\\Documents\\Cerveau Alix\\_Unification_Alix\\src\\alix\\cortex_c99\\tower7b_vocab.bin";

    alix_vocab_t vocab;
    if (!alix_vocab_load(&vocab, vocab_path)) return 1;

    alix_laser_file_t file;
    if (!alix_laser_open(&file, gguf_path, ALIX_IO_MMAP)) return 1;

    int prompt_tokens[] = { 1, 894, 584, 751, 1808, 707, 425, 27073, 316, 425, 3444, 1577, 13, 29934, 29948, 1713, 584 };
    int n_prompt = sizeof(prompt_tokens) / sizeof(prompt_tokens[0]);

    printf("==============================================================================\n");
    printf("  🏛️⚡ C-ALIX : VRAIE LECTURE CHIRURGICALE (GATE + UP + DOWN COUPÉS !)\n");
    printf("  Table d'interrupteurs transférée de ProSparse-7B -> TowerInstruct-7B\n");
    printf("==============================================================================\n\n");

    float* k_cache  = (float*)calloc((size_t)NUM_LAYERS * MAX_SEQ_LEN * DIM_KV, sizeof(float));
    float* v_cache  = (float*)calloc((size_t)NUM_LAYERS * MAX_SEQ_LEN * DIM_KV, sizeof(float));
    float* x        = (float*)malloc(DIM_MODEL * sizeof(float));
    float* x_norm   = (float*)malloc(DIM_MODEL * sizeof(float));
    float* q_vec    = (float*)malloc(DIM_MODEL * sizeof(float));
    float* attn_o   = (float*)malloc(DIM_MODEL * sizeof(float));
    float* h_sparse = (float*)malloc(SPITFIRE_MAX_K * sizeof(float));

    const uint8_t* raw_emb = (const uint8_t*)alix_laser_mmap_pointer(&file, TOWER7B_TOKEN_EMBD_OFF);
    const float*   w_out_norm = (const float*)alix_laser_mmap_pointer(&file, TOWER7B_OUTPUT_NORM_OFF);
    const uint8_t* raw_out = (const uint8_t*)alix_laser_mmap_pointer(&file, TOWER7B_OUTPUT_OFF);

    const char* kv_cache_file = "C:\\Users\\Christian\\Documents\\Cerveau Alix\\_Unification_Alix\\src\\alix\\cortex_c99\\tower7b_prefill_kv.bin";
    size_t kv_bytes = (size_t)NUM_LAYERS * MAX_SEQ_LEN * DIM_KV * sizeof(float);
    FILE* fkv = fopen(kv_cache_file, "rb");
    if (fkv) {
        fread(k_cache, 1, kv_bytes, fkv);
        fread(v_cache, 1, kv_bytes, fkv);
        fclose(fkv);
    }

    int k_tests[6]     = { 512, 256, 160, 128, 80, 64 };
    float alphas[6]    = { 1.00f, 1.00f, 1.00f, 1.00f, 1.00f, 1.00f };

    for (int t = 0; t < 6; ++t) {
        int k_val = k_tests[t];
        float alpha = alphas[t];
        uint64_t ffn_bytes = 0;
        double t0 = get_time_ms();

        int pos = n_prompt - 1;
        int tid = prompt_tokens[pos];
        const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_emb + (size_t)tid * ROW_BYTES_4096_Q4K);
        for (int sb = 0; sb < BLOCKS_PER_ROW_4096; ++sb) {
            dequantize_q4_K_block(&emb_row[sb], x + sb * 256);
        }

        for (int l = 0; l < NUM_LAYERS; ++l) {
            int k_layer = k_val;
            forward_one_layer_true_laser(&file, l, pos, x, k_cache, v_cache, k_layer, alpha, x_norm, q_vec, attn_o, h_sparse, &ffn_bytes);
        }

        alix_rmsnorm(x, w_out_norm, x_norm, DIM_MODEL);
        int top5_tid[5] = {0, 0, 0, 0, 0};
        float top5_lg[5] = {-1e30f, -1e30f, -1e30f, -1e30f, -1e30f};
        float lg_paris = -1e30f;
        int rank_paris = 1;

        for (int v = 0; v < VOCAB_SIZE; ++v) {
            const block_q6_K_t* out_row = (const block_q6_K_t*)(raw_out + (size_t)v * ROW_BYTES_4096_Q6K);
            float lg = dot_q6_K_row4096(out_row, x_norm);
            if (v == 3681) lg_paris = lg;
            for (int k = 0; k < 5; ++k) {
                if (lg > top5_lg[k]) {
                    for (int s = 4; s > k; --s) {
                        top5_lg[s] = top5_lg[s - 1];
                        top5_tid[s] = top5_tid[s - 1];
                    }
                    top5_lg[k] = lg;
                    top5_tid[k] = v;
                    break;
                }
            }
        }
        for (int v = 0; v < VOCAB_SIZE; ++v) {
            const block_q6_K_t* out_row = (const block_q6_K_t*)(raw_out + (size_t)v * ROW_BYTES_4096_Q6K);
            float lg = dot_q6_K_row4096(out_row, x_norm);
            if (lg > lg_paris) rank_paris++;
        }

        double dt_s = (get_time_ms() - t0) / 1000.0;
        printf("  [VRAI LASER (Gate+Up+Down coupés) K = %3d neurones (%4.1f%%) | alpha = %.2f]\n", k_val, (float)k_val * 100.0f / 11008.0f, alpha);
        printf("    • Temps total (32 couches) : %.3f s ! (FFN lu : %.1f Mo au lieu de 2650 Mo)\n", dt_s, (double)ffn_bytes / (1024.0 * 1024.0));
        printf("    • ' Paris' (#3681)         : Logit = %6.2f | Rang = #%d / 32007\n", lg_paris, rank_paris);
        printf("    • Top-5 : ");
        for (int k = 0; k < 5; ++k) {
            char tbuf[64];
            alix_vocab_get_token(&vocab, top5_tid[k], tbuf, sizeof(tbuf));
            printf("#%d '%s' (%.2f) | ", k + 1, tbuf, top5_lg[k]);
        }
        printf("\n\n");
        fflush(stdout);
    }

    alix_laser_close(&file);
    return 0;
}
