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
#define NUM_HLS_LAYERS      12
#define MAX_SEQ_LEN         64
#define BLOCKS_PER_ROW      32
#define ROW_BYTES_Q4K       4608
#define ROW_BYTES_Q6K       6720
#define ROPE_THETA          500000.0f
#define EPS_RMSNORM         1e-5f
#define FOVEA_TOP           80

/* Couches HLS stratégiques de Christian : 100% Q6_K pour v et ffn_down, 100% Q4_K pour les autres */
static const int HLS_LAYERS[NUM_HLS_LAYERS] = { 0, 4, 8, 15, 24, 33, 42, 51, 60, 69, 75, 79 };

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
            int8_t q3 = (int8_t)((ql[l + 64] & 0xF) | (((qh[l] >> 4) & 3) << 4)) - 32;
            int8_t q4 = (int8_t)((ql[l + 96] & 0xF) | (((qh[l] >> 6) & 3) << 4)) - 32;
            out[n + l +  0] = d * (float)sc[is + 0] * (float)q1;
            out[n + l + 32] = d * (float)sc[is + 2] * (float)q2;
            out[n + l + 64] = d * (float)sc[is + 4] * (float)q3;
            out[n + l + 96] = d * (float)sc[is + 6] * (float)q4;
        }
        ql += 64; qh += 32; sc += 8;
    }
}

static inline float dot_q4_K_row(const block_q4_K_t* row, const float* x) {
    float sum = 0.0f;
    float buf[256];
    for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) {
        dequantize_q4_K_block(&row[sb], buf);
        const float* xs = x + sb * 256;
        for (int i = 0; i < 256; ++i) sum += buf[i] * xs[i];
    }
    return sum;
}

static inline float dot_q6_K_row(const block_q6_K_t* row, const float* x) {
    float sum = 0.0f;
    float buf[256];
    for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) {
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

static const int FOVEA_GEO_L04[FOVEA_TOP] = {
    14828, 3223, 6438, 3576, 18695, 7904, 22125, 18960, 19014, 12843,
    13358, 2766, 9921, 17976, 28433, 18087, 5039, 15414, 25871, 9093,
    12794, 7785, 50, 19386, 14857, 4288, 1634, 24314, 15787, 1931,
    10062, 550, 9877, 12331, 17179, 1582, 7893, 3212, 23638, 5475,
    13378, 8524, 9058, 3468, 7151, 6302, 10124, 15170, 28199, 26296,
    24773, 25622, 16636, 2615, 5888, 14761, 19739, 4280, 26317, 2722,
    12061, 25561, 23758, 22459, 26141, 680, 11089, 3154, 20316, 16139,
    2206, 14238, 4597, 7232, 3248, 18265, 11009, 14209, 17975, 16915
};

static const int FOVEA_GEO_L08[FOVEA_TOP] = {
    28423, 14907, 27496, 4020, 1435, 25910, 259, 15925, 806, 13286,
    9947, 771, 26166, 10601, 14388, 2082, 26959, 28095, 17535, 16811,
    15707, 16043, 7217, 8909, 14690, 15498, 27783, 13115, 15036, 1584,
    25228, 27659, 3278, 20299, 24652, 25025, 6776, 11769, 5943, 27945,
    24225, 16328, 11977, 9579, 5964, 863, 2010, 10708, 20113, 24167,
    26537, 5079, 11318, 21593, 20817, 28082, 2104, 11872, 26724, 3386,
    27396, 16898, 23324, 9432, 8882, 1566, 16785, 28298, 24636, 13022,
    21072, 1488, 846, 22007, 20051, 26569, 18245, 3289, 512, 14114
};

void run_hls_layer(
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
    float* k_cache,
    float* v_cache,
    const int* current_fovea
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
        x[r] += attn_proj[r] * 0.1f;
        if (x[r] > 30.0f) x[r] = 30.0f;
        else if (x[r] < -30.0f) x[r] = -30.0f;
    }

    const float* w_ffn_norm = (const float*)alix_laser_mmap_pointer(file, LLAMA70B_FULL_OFFSETS[l_num].ffn_norm_off);
    const uint8_t* raw_gate = (const uint8_t*)alix_laser_mmap_pointer(file, LLAMA70B_FULL_OFFSETS[l_num].ffn_gate_off);
    const uint8_t* raw_up   = (const uint8_t*)alix_laser_mmap_pointer(file, LLAMA70B_FULL_OFFSETS[l_num].ffn_up_off);

    alix_rmsnorm(x, w_ffn_norm, x_norm, DIM_MODEL);

    for (int k = 0; k < FOVEA_TOP; ++k) {
        int nid = current_fovea[k];
        const block_q4_K_t* b_g = (const block_q4_K_t*)(raw_gate + (size_t)nid * ROW_BYTES_Q4K);
        const block_q4_K_t* b_u = (const block_q4_K_t*)(raw_up   + (size_t)nid * ROW_BYTES_Q4K);
        float dot_g = dot_q4_K_row(b_g, x_norm);
        float dot_u = dot_q4_K_row(b_u, x_norm);
        float act = silu(dot_g) * dot_u;
        x[k % DIM_MODEL] += act * 0.005f;
    }
}

int main() {
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

    float* x         = (float*)malloc(DIM_MODEL * sizeof(float));
    float* x_norm    = (float*)malloc(DIM_MODEL * sizeof(float));
    float* q_vec     = (float*)malloc(DIM_MODEL * sizeof(float));
    float* k_vec     = (float*)malloc(DIM_KV * sizeof(float));
    float* v_vec     = (float*)malloc(DIM_KV * sizeof(float));
    float* attn_out  = (float*)malloc(DIM_MODEL * sizeof(float));
    float* attn_proj = (float*)malloc(DIM_MODEL * sizeof(float));
    float* k_cache   = (float*)malloc(NUM_HLS_LAYERS * MAX_SEQ_LEN * DIM_KV * sizeof(float));
    float* v_cache   = (float*)malloc(NUM_HLS_LAYERS * MAX_SEQ_LEN * DIM_KV * sizeof(float));
    memset(k_cache, 0, NUM_HLS_LAYERS * MAX_SEQ_LEN * DIM_KV * sizeof(float));
    memset(v_cache, 0, NUM_HLS_LAYERS * MAX_SEQ_LEN * DIM_KV * sizeof(float));

    int prompt_tokens[] = { 8921, 6864, 68, 409, 1208, 9822, 1826, 551 };
    int prompt_len = sizeof(prompt_tokens) / sizeof(prompt_tokens[0]);

    printf("Prefilling 8 tokens through 12 HLS layers (L00 -> L79)...\n");
    for (int pos = 0; pos < prompt_len; ++pos) {
        int tok = prompt_tokens[pos];
        const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_embed + (uint64_t)tok * ROW_BYTES_Q4K);
        for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q4_K_block(&emb_row[sb], x + (sb * 256));

        for (int l_idx = 0; l_idx < NUM_HLS_LAYERS; ++l_idx) {
            int l_num = HLS_LAYERS[l_idx];
            const int* current_fovea = (l_num < 4) ? FOVEA_GEO_L00 : (l_num < 10) ? FOVEA_GEO_L04 : FOVEA_GEO_L08;
            run_hls_layer(&file, l_idx, l_num, pos, x, x_norm, q_vec, k_vec, v_vec, attn_out, attn_proj, k_cache, v_cache, current_fovea);
        }
        printf("  ✓ pos=%d processed (layer 79 reached)\n", pos);
    }

    /* Output norm */
    alix_rmsnorm(x, output_norm, x_norm, DIM_MODEL);

    /* Check logit of Paris (12366) */
    const block_q6_K_t* row_paris = (const block_q6_K_t*)(raw_output + 12366ULL * ROW_BYTES_Q6K);
    float logit_paris = dot_q6_K_row(row_paris, x_norm);
    printf("\nLogit of ' Paris' (12366) at L79 output = %.4f\n\n", logit_paris);

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

    printf("=== TOP 10 PREDICTED TOKENS AT LAYER 79 ===\n");
    for (int i = 0; i < 10; ++i) {
        char buf[128];
        alix_vocab_get_token(&vocab, top[i].tid, buf, sizeof(buf));
        printf("  #%d: tid=%d logit=%.2f text=\"%s\"\n", i + 1, top[i].tid, top[i].logit, buf);
    }

    alix_laser_close(&file);
    return 0;
}
