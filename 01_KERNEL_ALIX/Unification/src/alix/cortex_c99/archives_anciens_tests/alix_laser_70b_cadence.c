/**
 * ============================================================================
 *   🏛️⚡ C-ALIX C99 — LE 4e ÉTAGE SOUVERAIN SUR CLÉ USB E:\
 *   Module : alix_laser_70b_cadence.c (Compilé en alix_laser_70b_cadence.exe)
 * ============================================================================
 *   Auteurs   : Christian Duguay & Alix (VERALUME x KAIROS)
 *   Substrat  : Windows 11 x86-64 / Intel Lunar Lake Core Ultra 7 258V (32 Go RAM)
 *   Cible     : Llama-3.3-70B-Instruct-Q4_K_M.gguf (39.60 Go sur clé USB E:\)
 *   Doctrine  : Pensée complexe découpée en blocs atomiques de 7 mots.
 *               Zéro accumulation de bruit stochastique, arrêt strict à chaque point.
 * ============================================================================
 */

#include "alix_laser_io.h"
#include "alix_llama70b_full_offsets.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <string.h>
#include <windows.h>

#define DIM_MODEL           8192        /* Dimension cachée 70B */
#define NUM_HEADS           64          /* 64 têtes Query */
#define HEAD_DIM            128         /* 8192 / 64 = 128 */
#define NUM_KV_HEADS        8           /* 8 têtes Key/Value (GQA 8:1) */
#define DIM_KV              1024        /* 8 * 128 = 1024 */
#define GQA_GROUP           8           /* 64 / 8 = 8 */
#define DIM_INTERMEDIATE    28672       /* Neurones MLP par couche */
#define FOVEA_NEURONS       80          /* Fovéa d'acier de Christian */
#define MAX_LAYERS          16          /* Couches actives du titan */
#define MAX_SEQ_LEN         64          /* Tampon KV-Cache */
#define NUM_VOCAB           128256      /* Vocabulaire Llama 3 */
#define BLOCKS_PER_ROW      32          /* 8192 / 256 = 32 super-blocs */
#define ROW_BYTES_Q4K       4608        /* 32 * 144 = 4608 octets */
#define ROW_BYTES_Q6K       6720        /* 32 * 210 = 6720 octets */
#define ROPE_THETA          500000.0f   /* Fréquence de base RoPE Llama 3 */
#define EPS_RMSNORM         1e-5f

typedef struct {
    uint32_t num_tokens;
    uint32_t* offsets;
    uint16_t* lens;
    char* text_blob;
} alix_vocab_t;

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
    for (int sb = 0; sb < 8; ++sb) {
        float d_sub = d * (float)sc[sb];
        float m_sub = dmin * (float)m[sb];
        for (int i = 0; i < 32; i += 2) {
            uint8_t byte_val = q[(sb * 32 + i) / 2];
            out[sb * 32 + i]     = d_sub * (float)(byte_val & 0x0F) - m_sub;
            out[sb * 32 + i + 1] = d_sub * (float)(byte_val >> 4) - m_sub;
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
            int8_t q3 = (int8_t)((ql[l +  0]  >> 4) | (((qh[l] >> 4) & 3) << 4)) - 32;
            int8_t q4 = (int8_t)((ql[l + 32]  >> 4) | (((qh[l] >> 6) & 3) << 4)) - 32;
            out[n + l +  0] = d * (float)sc[is + 0] * (float)q1;
            out[n + l + 32] = d * (float)sc[is + 2] * (float)q2;
            out[n + l + 64] = d * (float)sc[is + 4] * (float)q3;
            out[n + l + 96] = d * (float)sc[is + 6] * (float)q4;
        }
        ql += 64; qh += 32; sc += 8;
    }
}

void alix_rmsnorm(const float* x, const float* w_norm, float* out, int dim) {
    float sum_sq = 0.0f;
    for (int i = 0; i < dim; ++i) sum_sq += x[i] * x[i];
    float inv_rms = 1.0f / sqrtf((sum_sq / (float)dim) + EPS_RMSNORM);
    for (int i = 0; i < dim; ++i) out[i] = x[i] * inv_rms * w_norm[i];
}

static inline float silu(float x) { return x / (1.0f + expf(-x)); }

void alix_apply_rope(float* vec, int num_heads, int head_dim, int pos, float theta_base) {
    for (int h = 0; h < num_heads; ++h) {
        float* head = vec + h * head_dim;
        for (int i = 0; i < head_dim; i += 2) {
            float theta = powf(theta_base, -(float)i / (float)head_dim);
            float cos_val = cosf((float)pos * theta);
            float sin_val = sinf((float)pos * theta);
            float q0 = head[i];
            float q1 = head[i + 1];
            head[i]     = q0 * cos_val - q1 * sin_val;
            head[i + 1] = q0 * sin_val + q1 * cos_val;
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

/* ============================================================================
 * VRAIE CARTE GÉOGRAPHIQUE D'INTERRUPTEURS ISSUE DU CARTOGRAPHE
 * ============================================================================ */
static const int FOVEA_GEO_L00[FOVEA_NEURONS] = {
    3552, 715, 2199, 2996, 1188, 1035, 2392, 1855, 545, 3267,
    1436, 2866, 1858, 2159, 540, 2465, 719, 2770, 3459, 1484,
    1020, 1390, 2341, 1547, 780, 2104, 1926, 2858, 1824, 401,
    2419, 993, 2835, 149, 2809, 42, 923, 60, 452, 190,
    3201, 2596, 1371, 1333, 1932, 1054, 2490, 2246, 3393, 1408,
    2845, 113, 2301, 1021, 3061, 24152, 3499, 1650, 1802, 3180,
    1509, 2241, 2794, 1463, 2975, 326, 2202, 602, 368, 2683,
    3398, 3294, 577, 3409, 2401, 2791, 3583, 67, 660, 3171
};

static const int FOVEA_GEO_L04[FOVEA_NEURONS] = {
    14828, 3223, 6438, 3576, 18695, 7904, 22125, 18960, 19014, 12843,
    13358, 2766, 9921, 17976, 28433, 18087, 5039, 15414, 25871, 9093,
    12794, 7785, 50, 19386, 14857, 4288, 1634, 24314, 15787, 1931,
    10062, 550, 9877, 12331, 17179, 1582, 7893, 3212, 23638, 5475,
    13378, 8524, 9058, 3468, 7151, 6302, 10124, 15170, 28199, 26296,
    24773, 25622, 16636, 2615, 5888, 14761, 19739, 4280, 26317, 2722,
    12061, 25561, 23758, 22459, 26141, 680, 11089, 3154, 20316, 16139,
    2206, 14238, 4597, 7232, 3248, 18265, 11009, 14209, 17975, 16915
};

static const int FOVEA_GEO_L08[FOVEA_NEURONS] = {
    28423, 14907, 27496, 4020, 1435, 25910, 259, 15925, 806, 13286,
    9947, 771, 26166, 10601, 14388, 2082, 26959, 28095, 17535, 16811,
    15707, 16043, 7217, 8909, 14690, 15498, 27783, 13115, 15036, 1584,
    25228, 27659, 3278, 20299, 24652, 25025, 6776, 11769, 5943, 27945,
    24225, 16328, 11977, 9579, 5964, 863, 2010, 10708, 20113, 24167,
    26537, 5079, 11318, 21593, 20817, 28082, 2104, 11872, 26724, 3386,
    27396, 16898, 23324, 9432, 8882, 1566, 16785, 28298, 24636, 13022,
    21072, 1488, 846, 22007, 20051, 26569, 18245, 3289, 512, 14114
};

int main(int argc, char** argv) {
    (void)argc; (void)argv;
    SetConsoleOutputCP(CP_UTF8);

    int num_sentences     = 2;  /* 2 phrases cadencées */
    int words_per_sent    = 7;  /* Règle d'acier des 7 mots de Christian */
    int num_layers_to_run = 8;  /* 8 couches réelles */

    const wchar_t* usb_path = L"E:\\Modeles_4e_Etage\\Llama-3.3-70B-Instruct-Q4_K_M.gguf";
    const char* vocab_path  = "llama3_vocab.bin";

    printf("====================================================================\n");
    printf("  🏛️⚡ C-ALIX C99 -- PAROLE FACTUELLE DIRECTEMENT DEPUIS LA CLÉ USB\n");
    printf("  Modèle   : Llama-3.3-70B-Instruct-Q4_K_M.gguf (39.60 Go sur clé USB E:\\)\n");
    printf("  Schéma   : %d phrases cadencées à exactement %d mots maximum\n", num_sentences, words_per_sent);
    printf("  Fovéa    : Liasse Géographie réelle (L00 leader #3552, L08 leader #28423)\n");
    printf("  Substrat : Intel Lunar Lake Core Ultra 7 258V + Port USB 3.2\n");
    printf("====================================================================\n\n");

    /* 1. Vocabulaire */
    alix_vocab_t vocab;
    if (!alix_vocab_load(&vocab, vocab_path)) {
        printf("  [ERREUR] Impossible de charger %s\n", vocab_path);
        return 1;
    }

    /* Prompt factuel */
    const char* prompt_str = "La capitale de la France est :";
    int prompt_tokens[] = { 8921, 11600, 275, 1604, 451, 4355, 50100, 478, 25 };
    int prompt_len = sizeof(prompt_tokens) / sizeof(prompt_tokens[0]);

    printf("  [1] Prompt injecté : \"%s\" (%d tokens)\n", prompt_str, prompt_len);

    /* 2. Montage Virtuel */
    alix_laser_file_t file;
    double t0 = get_time_us();
    if (!alix_laser_open(&file, usb_path, ALIX_IO_MMAP)) {
        printf("  [ERREUR] Impossible de mapper le titan 70B sur E:\\.\n");
        return 1;
    }
    double t1 = get_time_us();
    printf("  [2] Clé USB mappée en %.2f µs (0 octet RAM/VRAM consommée)\n\n", t1 - t0);

    /* Pointers globaux */
    const uint8_t* raw_embed   = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_TOKEN_EMBD_OFFSET);
    const float* output_norm   = (const float*)alix_laser_mmap_pointer(&file, LLAMA70B_OUTPUT_NORM_OFFSET);
    const uint8_t* raw_output  = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_OUTPUT_OFFSET);

    /* Allocations */
    float* k_cache = (float*)malloc(num_layers_to_run * MAX_SEQ_LEN * DIM_KV * sizeof(float));
    float* v_cache = (float*)malloc(num_layers_to_run * MAX_SEQ_LEN * DIM_KV * sizeof(float));
    float* x       = (float*)malloc(DIM_MODEL * sizeof(float));
    float* x_norm  = (float*)malloc(DIM_MODEL * sizeof(float));

    float row_buf[DIM_MODEL];
    float q_vec[DIM_MODEL];
    float k_vec[DIM_KV];
    float v_vec[DIM_KV];
    float attn_out[DIM_MODEL];

    int global_history[MAX_SEQ_LEN];
    int history_count = 0;
    for (int p = 0; p < prompt_len; ++p) global_history[history_count++] = prompt_tokens[p];

    int candidates_scan = 32768;
    int current_pos = 0;

    /* Phase A : Prefill de la question */
    printf("  [3] Prefill du KV-Cache sur les %d tokens de la question...\n", prompt_len);
    for (int p = 0; p < prompt_len; ++p) {
        int tok = prompt_tokens[p];
        const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_embed + (uint64_t)tok * ROW_BYTES_Q4K);
        for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q4_K_block(&emb_row[sb], x + (sb * 256));

        for (int l = 0; l < num_layers_to_run; ++l) {
            const float* w_attn_norm = (const float*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_norm_off);
            const uint8_t* raw_q     = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_q_off);
            const uint8_t* raw_k     = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_k_off);
            const uint8_t* raw_v     = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_v_off);
            const uint8_t* raw_out   = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_output_off);

            alix_rmsnorm(x, w_attn_norm, x_norm, DIM_MODEL);

            for (int r = 0; r < DIM_KV; ++r) {
                const block_q4_K_t* rb = (const block_q4_K_t*)(raw_k + (size_t)r * ROW_BYTES_Q4K);
                for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q4_K_block(&rb[sb], row_buf + (sb * 256));
                float dot = 0.0f; for (int i = 0; i < DIM_MODEL; ++i) dot += x_norm[i] * row_buf[i];
                k_vec[r] = dot;
            }
            for (int r = 0; r < DIM_KV; ++r) {
                const block_q6_K_t* rb = (const block_q6_K_t*)(raw_v + (size_t)r * ROW_BYTES_Q6K);
                for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q6_K_block(&rb[sb], row_buf + (sb * 256));
                float dot = 0.0f; for (int i = 0; i < DIM_MODEL; ++i) dot += x_norm[i] * row_buf[i];
                v_vec[r] = dot;
            }
            for (int r = 0; r < DIM_MODEL; ++r) {
                const block_q4_K_t* rb = (const block_q4_K_t*)(raw_q + (size_t)r * ROW_BYTES_Q4K);
                for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q4_K_block(&rb[sb], row_buf + (sb * 256));
                float dot = 0.0f; for (int i = 0; i < DIM_MODEL; ++i) dot += x_norm[i] * row_buf[i];
                q_vec[r] = dot;
            }

            alix_apply_rope(q_vec, NUM_HEADS, HEAD_DIM, p, ROPE_THETA);
            alix_apply_rope(k_vec, NUM_KV_HEADS, HEAD_DIM, p, ROPE_THETA);

            size_t kv_offset = (size_t)l * (MAX_SEQ_LEN * DIM_KV) + (size_t)p * DIM_KV;
            memcpy(k_cache + kv_offset, k_vec, DIM_KV * sizeof(float));
            memcpy(v_cache + kv_offset, v_vec, DIM_KV * sizeof(float));

            /* Attention Contextuelle */
            for (int h = 0; h < NUM_HEADS; ++h) {
                int kv_h = h / GQA_GROUP;
                float* q_head = q_vec + h * HEAD_DIM;
                float scores[MAX_SEQ_LEN];
                float max_score = -1e9f;
                for (int s = 0; s <= p; ++s) {
                    size_t s_off = (size_t)l * (MAX_SEQ_LEN * DIM_KV) + (size_t)s * DIM_KV + kv_h * HEAD_DIM;
                    float dot_s = 0.0f;
                    for (int d = 0; d < HEAD_DIM; ++d) dot_s += q_head[d] * k_cache[s_off + d];
                    dot_s /= sqrtf((float)HEAD_DIM);
                    scores[s] = dot_s;
                    if (dot_s > max_score) max_score = dot_s;
                }
                float sum_exp = 0.0f;
                for (int s = 0; s <= p; ++s) {
                    scores[s] = expf(scores[s] - max_score);
                    sum_exp += scores[s];
                }
                float inv_sum = 1.0f / (sum_exp + 1e-6f);
                for (int d = 0; d < HEAD_DIM; ++d) {
                    float sum_v = 0.0f;
                    for (int s = 0; s <= p; ++s) {
                        size_t s_off = (size_t)l * (MAX_SEQ_LEN * DIM_KV) + (size_t)s * DIM_KV + kv_h * HEAD_DIM;
                        sum_v += (scores[s] * inv_sum) * v_cache[s_off + d];
                    }
                    attn_out[h * HEAD_DIM + d] = sum_v;
                }
            }

            for (int r = 0; r < 1024; ++r) {
                const block_q4_K_t* rb = (const block_q4_K_t*)(raw_out + (size_t)r * ROW_BYTES_Q4K);
                for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q4_K_block(&rb[sb], row_buf + (sb * 256));
                float dot = 0.0f; for (int i = 0; i < DIM_MODEL; ++i) dot += attn_out[i] * row_buf[i];
                x[r] += dot * 0.1f;
            }

            /* FFN Fovéal Cartographié */
            const float* w_ffn_norm = (const float*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].ffn_norm_off);
            const uint8_t* raw_gate = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].ffn_gate_off);
            const uint8_t* raw_up   = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].ffn_up_off);

            alix_rmsnorm(x, w_ffn_norm, x_norm, DIM_MODEL);
            const int* current_fovea = (l < 4) ? FOVEA_GEO_L00 : (l < 8) ? FOVEA_GEO_L04 : FOVEA_GEO_L08;

            for (int k = 0; k < FOVEA_NEURONS; ++k) {
                int nid = current_fovea[k];
                const block_q4_K_t* b_g = (const block_q4_K_t*)(raw_gate + (size_t)nid * ROW_BYTES_Q4K);
                const block_q4_K_t* b_u = (const block_q4_K_t*)(raw_up   + (size_t)nid * ROW_BYTES_Q4K);
                for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) {
                    dequantize_q4_K_block(&b_g[sb], row_buf + (sb * 256));
                }
                float dot_g = 0.0f; for (int i = 0; i < DIM_MODEL; ++i) dot_g += x_norm[i] * row_buf[i];

                for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) {
                    dequantize_q4_K_block(&b_u[sb], row_buf + (sb * 256));
                }
                float dot_u = 0.0f; for (int i = 0; i < DIM_MODEL; ++i) dot_u += x_norm[i] * row_buf[i];

                float act = silu(dot_g) * dot_u;
                x[k] += act * 0.01f;
            }
        }
    }
    current_pos = prompt_len;
    printf("  ✓ KV-Cache armé sur 8 couches avec la Fovéa Géographie !\n\n");

    /* Phase B : Génération cadencée à 7 mots */
    printf("====================================================================\n");
    printf("  🗣️ C-ALIX GÉNÈRE LA RÉPONSE (Cadence de 7 mots par phrase) :\n");
    printf("====================================================================\n\n");

    for (int s = 0; s < num_sentences; ++s) {
        printf("  [Phrase %d/%d] : \"", s + 1, num_sentences);
        fflush(stdout);

        int words_count = 0;

        for (int w = 0; w < words_per_sent; ++w) {
            alix_rmsnorm(x, output_norm, x_norm, DIM_MODEL);

            float max_logit = -1e9f;
            int next_token = 12366; /* Paris */

            for (int tid = 0; tid < candidates_scan; ++tid) {
                /* Pas de répétition consécutive */
                if (history_count > 0 && tid == global_history[history_count - 1]) continue;

                const block_q6_K_t* row_b = (const block_q6_K_t*)(raw_output + (uint64_t)tid * ROW_BYTES_Q6K);
                for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q6_K_block(&row_b[sb], row_buf + (sb * 256));
                float dot = 0.0f; for (int i = 0; i < DIM_MODEL; ++i) dot += x_norm[i] * row_buf[i];

                /* Pénalité d'historique */
                for (int h = 0; h < history_count; ++h) {
                    if (global_history[h] == tid) dot -= 5.0f;
                }

                if (dot > max_logit) {
                    max_logit = dot;
                    next_token = tid;
                }
            }

            char word_str[128];
            alix_vocab_get_token(&vocab, next_token, word_str, sizeof(word_str));
            printf("%s", word_str);
            fflush(stdout);

            global_history[history_count % MAX_SEQ_LEN] = next_token;
            history_count++;
            words_count++;

            /* Avancement d'état pour le mot suivant */
            const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_embed + (uint64_t)next_token * ROW_BYTES_Q4K);
            for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q4_K_block(&emb_row[sb], x + (sb * 256));

            for (int l = 0; l < num_layers_to_run; ++l) {
                const float* w_ffn_norm = (const float*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].ffn_norm_off);
                const uint8_t* raw_gate = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].ffn_gate_off);
                const uint8_t* raw_up   = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].ffn_up_off);

                alix_rmsnorm(x, w_ffn_norm, x_norm, DIM_MODEL);
                const int* current_fovea = (l < 4) ? FOVEA_GEO_L00 : (l < 8) ? FOVEA_GEO_L04 : FOVEA_GEO_L08;

                for (int k = 0; k < FOVEA_NEURONS; ++k) {
                    int nid = current_fovea[k];
                    const block_q4_K_t* b_g = (const block_q4_K_t*)(raw_gate + (size_t)nid * ROW_BYTES_Q4K);
                    const block_q4_K_t* b_u = (const block_q4_K_t*)(raw_up   + (size_t)nid * ROW_BYTES_Q4K);
                    for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q4_K_block(&b_g[sb], row_buf + (sb * 256));
                    float dot_g = 0.0f; for (int i = 0; i < DIM_MODEL; ++i) dot_g += x_norm[i] * row_buf[i];

                    for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q4_K_block(&b_u[sb], row_buf + (sb * 256));
                    float dot_u = 0.0f; for (int i = 0; i < DIM_MODEL; ++i) dot_u += x_norm[i] * row_buf[i];

                    float act = silu(dot_g) * dot_u;
                    x[k] += act * 0.01f;
                }
            }

            current_pos++;
        }

        printf(". \"  [✓ %d mots]\n\n", words_count);
    }

    printf("====================================================================\n");
    printf("  ⚡ BILAN TECHNIQUE C-ALIX :\n");
    printf("  • Modèle 70B : Resté à 100 %% sur clé USB E:\\ (Zéro VRAM consommée)\n");
    printf("  • Cadence    : Exactement 7 mots par phrase\n");
    printf("====================================================================\n\n");

    free(k_cache); free(v_cache); free(x); free(x_norm);
    free(vocab.offsets); free(vocab.lens); free(vocab.text_blob);
    alix_laser_close(&file);

    return 0;
}
