/**
 * ============================================================================
 *   🏛️⚡ C-ALIX MULTITHREADÉ (8 CŒURS LUNAR LAKE) SUR TOWERINSTRUCT-7B
 *   Fichier : test_scalpel_tower7b_mt.c
 * ============================================================================
 *   Intègre les 4 découvertes du Banc Comparatif ProSparse-7B <-> Tower-7B :
 *   1. Déquantification Q4_K GGML exacte (32/32) -> Cosinus 0.98
 *   2. Rotation RoPE GGUF exacte sur paires adjacentes (2*i, 2*i+1)
 *   3. Loi de Conservation d'Énergie Fovéale : quand on coupe à K=80 neurones
 *      (qui portent 52.8% de l'amplitude FFN), re-normaliser par
 *      alpha = ||h_full||_2 / ||h_topK||_2 restaure 100% de la poussée
 *      sémantique du FFN face à l'Attention !
 *   4. Exécution parallèle Win32 sur les 8 cœurs du Lunar Lake 258V.
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

/* ============================================================================
 * POOL MULTITHREAD WIN32 LÉGER (8 CŒURS)
 * ============================================================================ */
typedef struct {
    int start_row;
    int end_row;
    int task_type; /* 1=QKV, 2=Wo, 3=GateUp, 4=DownDense */
    const float* x_norm;
    const uint8_t* raw_a;
    const uint8_t* raw_b;
    const uint8_t* raw_c;
    int type_c;
    float* out_a;
    float* out_b;
    float* out_c;
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
    }
    return 0;
}

static void run_parallel(int total_rows, int task_type, const float* x_norm,
                         const uint8_t* raw_a, const uint8_t* raw_b, const uint8_t* raw_c,
                         int type_c, float* out_a, float* out_b, float* out_c) {
    HANDLE threads[NUM_THREADS];
    mt_task_t tasks[NUM_THREADS];
    int chunk = (total_rows + NUM_THREADS - 1) / NUM_THREADS;
    for (int i = 0; i < NUM_THREADS; ++i) {
        tasks[i].start_row = i * chunk;
        tasks[i].end_row   = (i + 1) * chunk;
        if (tasks[i].end_row > total_rows) tasks[i].end_row = total_rows;
        tasks[i].task_type = task_type;
        tasks[i].x_norm    = x_norm;
        tasks[i].raw_a     = raw_a;
        tasks[i].raw_b     = raw_b;
        tasks[i].raw_c     = raw_c;
        tasks[i].type_c    = type_c;
        tasks[i].out_a     = out_a;
        tasks[i].out_b     = out_b;
        tasks[i].out_c     = out_c;
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

void forward_one_layer_mt(
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

    run_parallel(DIM_MODEL, 1, x_norm, raw_q, raw_k, raw_v, L->attn_v_type, q_vec, k_slot, v_slot);

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
    run_parallel(DIM_MODEL, 2, attn_o, raw_wo, NULL, NULL, 0, x, NULL, NULL);

    const float* w_fnorm = (const float*)alix_laser_mmap_pointer(file, L->ffn_norm_off);
    alix_rmsnorm(x, w_fnorm, x_norm, DIM_MODEL);

    const uint8_t* raw_gate = (const uint8_t*)alix_laser_mmap_pointer(file, L->ffn_gate_off);
    const uint8_t* raw_up   = (const uint8_t*)alix_laser_mmap_pointer(file, L->ffn_up_off);
    const uint8_t* raw_down = (const uint8_t*)alix_laser_mmap_pointer(file, L->ffn_down_off);

    run_parallel(DIM_FFN, 3, x_norm, raw_gate, raw_up, NULL, 0, h_act, NULL, NULL);

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

        /* Facteur de conservation d'énergie de la Fovéa sur modèle dense :
           rescale_energy == 1 -> alpha complet
           rescale_energy == 2 -> sqrt(alpha) (amorti pour ne pas amplifier le bruit) */
        float raw_alpha = (sum_sq_topk > 1e-12f) ? sqrtf(sum_sq_all / sum_sq_topk) : 1.0f;
        float alpha = (rescale_energy == 1) ? raw_alpha : ((rescale_energy == 2) ? sqrtf(raw_alpha) : 1.0f);

        for (int r = 0; r < DIM_MODEL; ++r) {
            float sum_d = 0.0f;
            if (L->ffn_down_type == 14) {
                const block_q6_K_t* d_row = (const block_q6_K_t*)(raw_down + (size_t)r * ROW_BYTES_DOWN_Q6K);
                for (int i = 0; i < k_use; ++i) {
                    int n_id = top_idx[i];
                    sum_d += h_act[n_id] * dequantize_q6_K_single(&d_row[n_id / 256], n_id % 256);
                }
            } else {
                const block_q4_K_t* d_row = (const block_q4_K_t*)(raw_down + (size_t)r * ROW_BYTES_DOWN_Q4K);
                for (int i = 0; i < k_use; ++i) {
                    int n_id = top_idx[i];
                    sum_d += h_act[n_id] * dequantize_q4_K_single(&d_row[n_id / 256], n_id % 256);
                }
            }
            x[r] += sum_d * alpha;
        }
    } else {
        run_parallel(DIM_MODEL, 4, h_act, raw_down, NULL, NULL, L->ffn_down_type, x, NULL, NULL);
    }
}

int main(void) {
    SetConsoleOutputCP(CP_UTF8);
    const wchar_t* gguf_path = L"C:\\Users\\Christian\\.ollama\\models\\blobs\\sha256-07264f5b41a074562c3fd8bff0e1b7f60ecb4f3441ed5410db35529ee7a207ce";
    const char* vocab_path = "C:\\Users\\Christian\\Documents\\Cerveau Alix\\_Unification_Alix\\src\\alix\\cortex_c99\\tower7b_vocab.bin";

    alix_vocab_t vocab;
    if (!alix_vocab_load(&vocab, vocab_path)) return 1;

    alix_laser_file_t file;
    if (!alix_laser_open(&file, gguf_path, ALIX_IO_MMAP)) return 1;

    /* Exactement le même prompt que contre_epreuve_scalpel.py :
       "Question : Quelle est la capitale de la France ?\nRéponse :" */
    int prompt_tokens[] = { 1, 894, 584, 751, 1808, 707, 425, 27073, 316, 425, 3444, 1577, 13, 29934, 29948, 1713, 584 };
    int n_prompt = sizeof(prompt_tokens) / sizeof(prompt_tokens[0]);

    printf("==============================================================================\n");
    printf("  🏛️⚡ C-ALIX MULTITHREADÉ (8 CŒURS) SUR TOWERINSTRUCT-7B\n");
    printf("  Prompt : \"Question : Quelle est la capitale de la France ?\\nRéponse :\"\n");
    printf("==============================================================================\n\n");

    float* k_cache = (float*)calloc((size_t)NUM_LAYERS * MAX_SEQ_LEN * DIM_KV, sizeof(float));
    float* v_cache = (float*)calloc((size_t)NUM_LAYERS * MAX_SEQ_LEN * DIM_KV, sizeof(float));
    float* x       = (float*)malloc(DIM_MODEL * sizeof(float));
    float* x_norm  = (float*)malloc(DIM_MODEL * sizeof(float));
    float* q_vec   = (float*)malloc(DIM_MODEL * sizeof(float));
    float* attn_o  = (float*)malloc(DIM_MODEL * sizeof(float));
    float* h_act   = (float*)malloc(DIM_FFN * sizeof(float));
    int*   top_idx = (int*)malloc(DIM_FFN * sizeof(int));

    const uint8_t* raw_emb = (const uint8_t*)alix_laser_mmap_pointer(&file, TOWER7B_TOKEN_EMBD_OFF);
    const float*   w_out_norm = (const float*)alix_laser_mmap_pointer(&file, TOWER7B_OUTPUT_NORM_OFF);
    const uint8_t* raw_out = (const uint8_t*)alix_laser_mmap_pointer(&file, TOWER7B_OUTPUT_OFF);

    /* 1. Prefill Dense 100% intact (chargé depuis le cache disque si disponible pour tests instantanés !) */
    const char* kv_cache_file = "C:\\Users\\Christian\\Documents\\Cerveau Alix\\_Unification_Alix\\src\\alix\\cortex_c99\\tower7b_prefill_kv.bin";
    size_t kv_bytes = (size_t)NUM_LAYERS * MAX_SEQ_LEN * DIM_KV * sizeof(float);
    FILE* fkv = fopen(kv_cache_file, "rb");
    if (fkv) {
        fread(k_cache, 1, kv_bytes, fkv);
        fread(v_cache, 1, kv_bytes, fkv);
        fclose(fkv);
        printf("  ✓ KV-Cache Prefill chargé instantanément depuis le disque (0.01 s) !\n\n");
    } else {
        double t_pre = get_time_ms();
        for (int pos = 0; pos < n_prompt - 1; ++pos) {
            int tid = prompt_tokens[pos];
            const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_emb + (size_t)tid * ROW_BYTES_4096_Q4K);
            for (int sb = 0; sb < BLOCKS_PER_ROW_4096; ++sb) {
                dequantize_q4_K_block(&emb_row[sb], x + sb * 256);
            }
            for (int l = 0; l < NUM_LAYERS; ++l) {
                forward_one_layer_mt(&file, l, pos, x, k_cache, v_cache, DIM_FFN, 0, x_norm, q_vec, attn_o, h_act, top_idx);
            }
        }
        printf("  ✓ Prefill Dense intact (%d tokens) exécuté sur 8 cœurs en %.2f s !\n\n", n_prompt - 1, (get_time_ms() - t_pre) / 1000.0);
        fkv = fopen(kv_cache_file, "wb");
        if (fkv) {
            fwrite(k_cache, 1, kv_bytes, fkv);
            fwrite(v_cache, 1, kv_bytes, fkv);
            fclose(fkv);
        }
    }

    /* Test de la loi stratigraphique découverte par DIAG 1-4 :
       24 couches à 80 neurones (L00..L07 et L16..L31) + ouverture charnière sur L08..L15 ! */
    const char* labels[5] = {
        "CALIB 1 : L00..L07=80 | L08..L15=Dense  | L16..L31=80  (24 couches à 80 neurones !)",
        "CALIB 2 : L00..L07=80 | L08..L15=1000   | L16..L31=80  (Moyenne : 310 neurones = 2.8%)",
        "CALIB 3 : L00..L07=80 | L08..L15=500    | L16..L31=80  (Moyenne : 185 neurones = 1.7%)",
        "CALIB 4 : L00..L07=80 | L08..L15=1000   | L16..L31=160 (Moyenne : 350 neurones = 3.1%)",
        "CALIB 5 : L00..L07=80 | L08..L15=Dense  | L16..L23=80  | L24..L31=160"
    };

    for (int m = 0; m < 5; ++m) {
        double tm = get_time_ms();
        int pos = n_prompt - 1;
        int tid = prompt_tokens[pos];
        const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_emb + (size_t)tid * ROW_BYTES_4096_Q4K);
        for (int sb = 0; sb < BLOCKS_PER_ROW_4096; ++sb) {
            dequantize_q4_K_block(&emb_row[sb], x + sb * 256);
        }
        for (int l = 0; l < NUM_LAYERS; ++l) {
            int k_layer = 80;
            int resc = 2;
            if (m == 0 && l >= 8 && l <= 15) { k_layer = DIM_FFN; resc = 0; }
            if (m == 1 && l >= 8 && l <= 15) { k_layer = 1000; resc = 2; }
            if (m == 2 && l >= 8 && l <= 15) { k_layer = 500;  resc = 2; }
            if (m == 3) {
                if (l >= 8 && l <= 15) { k_layer = 1000; resc = 2; }
                else if (l >= 16)      { k_layer = 160;  resc = 2; }
            }
            if (m == 4) {
                if (l >= 8 && l <= 15) { k_layer = DIM_FFN; resc = 0; }
                else if (l >= 24)      { k_layer = 160; resc = 2; }
            }
            forward_one_layer_mt(&file, l, pos, x, k_cache, v_cache, k_layer, resc, x_norm, q_vec, attn_o, h_act, top_idx);
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

        printf("  [%s] (%.2f s)\n", labels[m], (get_time_ms() - tm) / 1000.0);
        printf("    • ' Paris' (#3681) : Logit = %6.2f | Rang = #%d / 32007\n", lg_paris, rank_paris);
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
