#include "alix_laser_io.h"
#include "alix_llama70b_full_offsets.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <string.h>

#define DIM_MODEL           8192
#define NUM_HEADS           64
#define HEAD_DIM            128
#define NUM_KV_HEADS        8
#define DIM_KV              1024
#define GQA_GROUP           8
#define MAX_SEQ_LEN         64
#define BLOCKS_PER_ROW_8192 32          /* 8192 / 256 = 32 */
#define BLOCKS_PER_ROW_DOWN 112         /* 28672 / 256 = 112 */
#define ROW_BYTES_Q4K       4608        /* 32 * 144 */
#define ROW_BYTES_Q6K       6720        /* 32 * 210 */
#define ROW_BYTES_DOWN_Q6K  23520       /* 112 * 210 */
#define ROPE_THETA          500000.0f
#define EPS_RMSNORM         1e-5f
#define FOVEA_TOP           80

/* Les 40 couches 100% Q6_K :
 * 0..9 (Entrée syntaxique complète)
 * 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48, 51, 54, 57, 60, 63, 66, 69 (Harmonique 1 sur 3)
 * 70..79 (Sortie sémantique et sondage terminal L77, L78, L79)
 */
#define NUM_LAYERS_40 40
static const int LAYERS_40[NUM_LAYERS_40] = {
     0,  1,  2,  3,  4,  5,  6,  7,  8,  9,
    12, 15, 18, 21, 24, 27, 30, 33, 36, 39,
    42, 45, 48, 51, 54, 57, 60, 63, 66, 69,
    70, 71, 72, 73, 74, 75, 76, 77, 78, 79
};

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

static inline float dequantize_q6_K_single(const block_q6_K_t* b, int i) {
    float d = fp16_to_fp32(b->d);
    int n = (i >= 128) ? 128 : 0;
    int idx = i - n;
    int l = idx % 32;
    int is = l / 16;
    const uint8_t* ql = b->ql + (n == 0 ? 0 : 64);
    const uint8_t* qh = b->qh + (n == 0 ? 0 : 32);
    const int8_t*  sc = b->scales + (n == 0 ? 0 : 8);

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

static inline float dot_q4_K_row(const block_q4_K_t* row, const float* x) {
    float sum = 0.0f;
    float buf[256];
    for (int sb = 0; sb < BLOCKS_PER_ROW_8192; ++sb) {
        dequantize_q4_K_block(&row[sb], buf);
        const float* xs = x + sb * 256;
        for (int i = 0; i < 256; ++i) sum += buf[i] * xs[i];
    }
    return sum;
}

static inline float dot_q6_K_row(const block_q6_K_t* row, const float* x) {
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

static inline float silu(float x) { return x / (1.0f + expf(-x)); }

void alix_apply_rope(float* vec, int num_heads, int head_dim, int pos, float theta_base) {
    int half_dim = head_dim / 2;
    for (int h = 0; h < num_heads; ++h) {
        float* head = vec + h * head_dim;
        for (int i = 0; i < half_dim; ++i) {
            float theta = powf(theta_base, -(float)(2 * i) / (float)head_dim);
            float cos_val = cosf((float)pos * theta);
            float sin_val = sinf((float)pos * theta);
            float x0 = head[i];
            float x1 = head[i + half_dim];
            head[i]            = x0 * cos_val - x1 * sin_val;
            head[i + half_dim] = x0 * sin_val + x1 * cos_val;
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

/* Fovéas cartographiées */
static const int FOVEA_GEO_L00[FOVEA_TOP] = {
    3552, 715, 2199, 2996, 1188, 1035, 2392, 1855, 545, 3267,
    1436, 2866, 1858, 2159, 540, 2465, 719, 2770, 3459, 1484,
    1020, 1390, 2341, 1547, 780, 2104, 1926, 2858, 1824, 401,
    2419, 993, 2835, 149, 2809, 42, 923, 60, 452, 190,
    3201, 2596, 1371, 1333, 1932, 1054, 2490, 2246, 3393, 1408,
    2845, 113, 2301, 1021, 3061, 24152, 3499, 1650, 1802, 3180,
    1509, 2241, 2794, 1463, 2975, 326, 2202, 602, 368, 2683,
    3398, 3294, 577, 3409, 2401, 2791, 3583, 67, 660, 3171
};

void run_layer_40(
    alix_laser_file_t* file,
    int l_idx,
    int l_num,
    int pos,
    float* x,
    float* x_norm,
    float* q_vec,
    float* k_vec,
    float* v_vec,
    float* attn_out,
    float* attn_proj,
    float* act_fovea,
    float* k_cache,
    float* v_cache,
    int compute_ffn
) {
    const float* w_attn_norm = (const float*)alix_laser_mmap_pointer(file, LLAMA70B_FULL_OFFSETS[l_num].attn_norm_off);
    const uint8_t* raw_q     = (const uint8_t*)alix_laser_mmap_pointer(file, LLAMA70B_FULL_OFFSETS[l_num].attn_q_off);
    const uint8_t* raw_k     = (const uint8_t*)alix_laser_mmap_pointer(file, LLAMA70B_FULL_OFFSETS[l_num].attn_k_off);
    const uint8_t* raw_v     = (const uint8_t*)alix_laser_mmap_pointer(file, LLAMA70B_FULL_OFFSETS[l_num].attn_v_off);
    const uint8_t* raw_out   = (const uint8_t*)alix_laser_mmap_pointer(file, LLAMA70B_FULL_OFFSETS[l_num].attn_output_off);

    alix_rmsnorm(x, w_attn_norm, x_norm, DIM_MODEL);

    for (int r = 0; r < DIM_KV; ++r) {
        const block_q4_K_t* row_b = (const block_q4_K_t*)(raw_k + (size_t)r * ROW_BYTES_Q4K);
        k_vec[r] = dot_q4_K_row(row_b, x_norm);
    }
    for (int r = 0; r < DIM_KV; ++r) {
        const block_q6_K_t* row_b = (const block_q6_K_t*)(raw_v + (size_t)r * ROW_BYTES_Q6K);
        v_vec[r] = dot_q6_K_row(row_b, x_norm);
    }
    for (int r = 0; r < DIM_MODEL; ++r) {
        const block_q4_K_t* row_b = (const block_q4_K_t*)(raw_q + (size_t)r * ROW_BYTES_Q4K);
        q_vec[r] = dot_q4_K_row(row_b, x_norm);
    }

    alix_apply_rope(q_vec, NUM_HEADS, HEAD_DIM, pos, ROPE_THETA);
    alix_apply_rope(k_vec, NUM_KV_HEADS, HEAD_DIM, pos, ROPE_THETA);

    size_t kv_offset = (size_t)l_idx * (MAX_SEQ_LEN * DIM_KV) + (size_t)pos * DIM_KV;
    memcpy(k_cache + kv_offset, k_vec, DIM_KV * sizeof(float));
    memcpy(v_cache + kv_offset, v_vec, DIM_KV * sizeof(float));

    for (int h = 0; h < NUM_HEADS; ++h) {
        int kv_h = h / GQA_GROUP;
        const float* q_head = q_vec + h * HEAD_DIM;
        float scores[MAX_SEQ_LEN];
        float max_score = -1e9f;

        for (int s = 0; s <= pos; ++s) {
            size_t s_off = (size_t)l_idx * (MAX_SEQ_LEN * DIM_KV) + (size_t)s * DIM_KV + kv_h * HEAD_DIM;
            const float* k_hist = k_cache + s_off;
            float dot_s = 0.0f;
            for (int d_i = 0; d_i < HEAD_DIM; ++d_i) dot_s += q_head[d_i] * k_hist[d_i];
            dot_s /= sqrtf((float)HEAD_DIM);
            scores[s] = dot_s;
            if (dot_s > max_score) max_score = dot_s;
        }

        float sum_exp = 0.0f;
        for (int s = 0; s <= pos; ++s) {
            scores[s] = expf(scores[s] - max_score);
            sum_exp += scores[s];
        }
        float inv_sum = 1.0f / (sum_exp + 1e-6f);

        for (int d_i = 0; d_i < HEAD_DIM; ++d_i) {
            float sum_v = 0.0f;
            for (int s = 0; s <= pos; ++s) {
                size_t s_off = (size_t)l_idx * (MAX_SEQ_LEN * DIM_KV) + (size_t)s * DIM_KV + kv_h * HEAD_DIM;
                sum_v += (scores[s] * inv_sum) * v_cache[s_off + d_i];
            }
            attn_out[h * HEAD_DIM + d_i] = sum_v;
        }
    }

    for (int r = 0; r < DIM_MODEL; ++r) {
        const block_q4_K_t* row_b = (const block_q4_K_t*)(raw_out + (size_t)r * ROW_BYTES_Q4K);
        attn_proj[r] = dot_q4_K_row(row_b, attn_out);
        x[r] += attn_proj[r];
    }

    if (!compute_ffn) return;

    /* FFN Fovéa */
    const float* w_ffn_norm = (const float*)alix_laser_mmap_pointer(file, LLAMA70B_FULL_OFFSETS[l_num].ffn_norm_off);
    const uint8_t* raw_gate = (const uint8_t*)alix_laser_mmap_pointer(file, LLAMA70B_FULL_OFFSETS[l_num].ffn_gate_off);
    const uint8_t* raw_up   = (const uint8_t*)alix_laser_mmap_pointer(file, LLAMA70B_FULL_OFFSETS[l_num].ffn_up_off);
    const uint8_t* raw_down = (const uint8_t*)alix_laser_mmap_pointer(file, LLAMA70B_FULL_OFFSETS[l_num].ffn_down_off);

    alix_rmsnorm(x, w_ffn_norm, x_norm, DIM_MODEL);

    /* 1. Calcul des 80 activations SwiGLU */
    for (int k = 0; k < FOVEA_TOP; ++k) {
        int nid = FOVEA_GEO_L00[k];
        const block_q4_K_t* b_g = (const block_q4_K_t*)(raw_gate + (size_t)nid * ROW_BYTES_Q4K);
        const block_q4_K_t* b_u = (const block_q4_K_t*)(raw_up   + (size_t)nid * ROW_BYTES_Q4K);
        float dot_g = dot_q4_K_row(b_g, x_norm);
        float dot_u = dot_q4_K_row(b_u, x_norm);
        act_fovea[k] = silu(dot_g) * dot_u;
    }

    /* 2. Rétro-projection ffn_down */
    for (int r = 0; r < DIM_MODEL; ++r) {
        const uint8_t* row_r = raw_down + (size_t)r * ROW_BYTES_DOWN_Q6K;
        float sum_down = 0.0f;
        for (int k = 0; k < FOVEA_TOP; ++k) {
            int nid = FOVEA_GEO_L00[k];
            int sb = nid / 256;
            int idx = nid % 256;
            const block_q6_K_t* b = (const block_q6_K_t*)(row_r + (size_t)sb * sizeof(block_q6_K_t));
            float w = dequantize_q6_K_single(b, idx);
            sum_down += act_fovea[k] * w;
        }
        x[r] += sum_down;
    }
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0); /* Flush immédiat pour voir les logs en direct ! */

    const wchar_t* usb_path = L"E:\\Modeles_4e_Etage\\Llama-3.3-70B-Instruct-Q4_K_M.gguf";
    alix_laser_file_t file;
    if (!alix_laser_open(&file, usb_path, ALIX_IO_MMAP)) {
        printf("Failed to open file.\n");
        return 1;
    }

    alix_vocab_t vocab;
    alix_vocab_load(&vocab, "llama3_vocab.bin");

    const uint8_t* raw_embed   = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_TOKEN_EMBD_OFFSET);
    const float* output_norm   = (const float*)alix_laser_mmap_pointer(&file, LLAMA70B_OUTPUT_NORM_OFFSET);
    const uint8_t* raw_output  = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_OUTPUT_OFFSET);

    float* x          = (float*)malloc(DIM_MODEL * sizeof(float));
    float* x_norm     = (float*)malloc(DIM_MODEL * sizeof(float));
    float* q_vec      = (float*)malloc(DIM_MODEL * sizeof(float));
    float* k_vec      = (float*)malloc(DIM_KV * sizeof(float));
    float* v_vec      = (float*)malloc(DIM_KV * sizeof(float));
    float* attn_out   = (float*)malloc(DIM_MODEL * sizeof(float));
    float* attn_proj  = (float*)malloc(DIM_MODEL * sizeof(float));
    float* act_fovea  = (float*)malloc(FOVEA_TOP * sizeof(float));
    float* k_cache    = (float*)malloc(NUM_LAYERS_40 * MAX_SEQ_LEN * DIM_KV * sizeof(float));
    float* v_cache    = (float*)malloc(NUM_LAYERS_40 * MAX_SEQ_LEN * DIM_KV * sizeof(float));
    memset(k_cache, 0, NUM_LAYERS_40 * MAX_SEQ_LEN * DIM_KV * sizeof(float));
    memset(v_cache, 0, NUM_LAYERS_40 * MAX_SEQ_LEN * DIM_KV * sizeof(float));

    /* Prompt complet avec Attention Sink <|begin_of_text|> (128000) */
    int prompt_tokens[] = { 128000, 8921, 6864, 68, 409, 1208, 9822, 1826, 551 };
    int prompt_len = sizeof(prompt_tokens) / sizeof(prompt_tokens[0]);

    printf("====================================================================\n");
    printf("🏛️⚡ C-ALIX : TEST DE LA LOI DE CHRISTIAN SUR 40 COUCHES Q6_K\n");
    printf("   10 Couches d'entrée (L00..L09) + 20 Harmoniques (L12..L69) + 10 Terminales (L70..L79)\n");
    printf("====================================================================\n");

    for (int pos = 0; pos < prompt_len; ++pos) {
        int tok = prompt_tokens[pos];
        const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_embed + (uint64_t)tok * ROW_BYTES_Q4K);
        for (int sb = 0; sb < BLOCKS_PER_ROW_8192; ++sb) dequantize_q4_K_block(&emb_row[sb], x + (sb * 256));

        /* Pour les tokens de pré-remplissage, on fait tourner l'Attention. Pour le token final ':', on active tout ! */
        for (int l_idx = 0; l_idx < NUM_LAYERS_40; ++l_idx) {
            int l_num = LAYERS_40[l_idx];
            /* Les 3 dernières couches sont simplement sondées (pas de FFN lourd) */
            int compute_ffn = (l_num < 77);
            run_layer_40(&file, l_idx, l_num, pos, x, x_norm, q_vec, k_vec, v_vec, attn_out, attn_proj, act_fovea, k_cache, v_cache, compute_ffn);
        }
        printf("  ✓ pos=%d (tok=%d) traite (x[0]=%.4f)\n", pos, tok, x[0]);
    }

    /* Output norm */
    alix_rmsnorm(x, output_norm, x_norm, DIM_MODEL);

    /* Check logit of Paris (12366) */
    const block_q6_K_t* row_paris = (const block_q6_K_t*)(raw_output + 12366ULL * ROW_BYTES_Q6K);
    float logit_paris = dot_q6_K_row(row_paris, x_norm);
    printf("\nLogit de ' Paris' (12366) a la sortie de L79 = %.4f\n\n", logit_paris);

    /* Top-10 tokens */
    typedef struct { int tid; float logit; } tok_score_t;
    tok_score_t top[10];
    for (int i = 0; i < 10; ++i) { top[i].tid = -1; top[i].logit = -1e9f; }

    for (int tid = 0; tid < 32768; ++tid) {
        const block_q6_K_t* row_b = (const block_q6_K_t*)(raw_output + (uint64_t)tid * ROW_BYTES_Q6K);
        float logit = dot_q6_K_row(row_b, x_norm);
        if (!isnan(logit)) {
            for (int i = 0; i < 10; ++i) {
                if (logit > top[i].logit) {
                    for (int j = 9; j > i; --j) top[j] = top[j - 1];
                    top[i].tid = tid;
                    top[i].logit = logit;
                    break;
                }
            }
        }
    }

    printf("=== TOP 10 DES MOTS PREDITS A LA COUCHE 79 ===\n");
    for (int i = 0; i < 10; ++i) {
        char buf[128];
        alix_vocab_get_token(&vocab, top[i].tid, buf, sizeof(buf));
        printf("  #%d: tid=%d logit=%.2f texte=\"%s\"\n", i + 1, top[i].tid, top[i].logit, buf);
    }

    alix_laser_close(&file);
    return 0;
}
