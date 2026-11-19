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
#define BLOCKS_PER_ROW_8192 32
#define ROW_BYTES_Q4K       4608
#define ROW_BYTES_Q5K       5632
#define ROW_BYTES_Q6K       6720
#define ROW_BYTES_DOWN_Q4K  16128
#define ROW_BYTES_DOWN_Q6K  23520
#define ROPE_THETA          500000.0f
#define EPS_RMSNORM         1e-5f
#define FOVEA_TOP           80

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
    int i  = idx % 32;
    float d_sub = d * (float)sc[sb];
    float m_sub = dmin * (float)m[sb];
    uint8_t byte_val = b->qs[(sb * 32 + i) / 2];
    uint8_t q_val = (i % 2 == 0) ? (byte_val & 0x0F) : (byte_val >> 4);
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
            float d1 = d * (float)sc[is + 0];
            float d2 = d * (float)sc[is + 2];
            float d3 = d * (float)sc[is + 4];
            float d4 = d * (float)sc[is + 6];
            out[n + l +  0] = d1 * (float)q1;
            out[n + l + 32] = d2 * (float)q2;
            out[n + l + 64] = d3 * (float)q3;
            out[n + l + 96] = d4 * (float)q4;
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

static inline float dot_q5_K_row(const block_q5_K_t* row, const float* x) {
    float sum = 0.0f;
    float buf[256];
    for (int sb = 0; sb < BLOCKS_PER_ROW_8192; ++sb) {
        dequantize_q5_K_block(&row[sb], buf);
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

static inline int is_q6k_layer(int l_num) {
    if (l_num < 10 || l_num >= 70) return 1;
    return (l_num % 3 == 0);
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);

    const wchar_t* usb_path = L"E:\\Modeles_4e_Etage\\Llama-3.3-70B-Instruct-Q4_K_M.gguf";
    alix_laser_file_t file;
    if (!alix_laser_open(&file, usb_path, ALIX_IO_MMAP)) {
        printf("Erreur mmap\n"); return 1;
    }

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
    float* k_cache    = (float*)malloc(80 * MAX_SEQ_LEN * DIM_KV * sizeof(float));
    float* v_cache    = (float*)malloc(80 * MAX_SEQ_LEN * DIM_KV * sizeof(float));
    memset(k_cache, 0, 80 * MAX_SEQ_LEN * DIM_KV * sizeof(float));
    memset(v_cache, 0, 80 * MAX_SEQ_LEN * DIM_KV * sizeof(float));

    /* Testons couche par couche sur 1 prompt */
    int prompt_tokens[] = { 128000, 8921, 6864, 68, 409, 1208, 9822, 1826, 551 };
    int prompt_len = sizeof(prompt_tokens) / sizeof(prompt_tokens[0]);

    printf("====================================================================\n");
    printf("  🎯 SONDE STRATIGRAPHIQUE COUCHE PAR COUCHE (L00 -> L79)\n");
    printf("  Mesure des logits à la sortie intermédiaire de chaque couche !\n");
    printf("====================================================================\n\n");

    const block_q6_K_t* row_paris = (const block_q6_K_t*)(raw_output + (uint64_t)12366 * ROW_BYTES_Q6K);
    const block_q6_K_t* row_mills = (const block_q6_K_t*)(raw_output + (uint64_t)34202 * ROW_BYTES_Q6K);
    const block_q6_K_t* row_france = (const block_q6_K_t*)(raw_output + (uint64_t)50100 * ROW_BYTES_Q6K);

    /* Embed token final ':' */
    for (int pos = 0; pos < prompt_len; ++pos) {
        int tok = prompt_tokens[pos];
        const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_embed + (uint64_t)tok * ROW_BYTES_Q4K);
        for (int sb = 0; sb < BLOCKS_PER_ROW_8192; ++sb) dequantize_q4_K_block(&emb_row[sb], x + (sb * 256));

        for (int l = 0; l < 80; ++l) {
            const float* w_attn_norm = (const float*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_norm_off);
            const uint8_t* raw_q     = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_q_off);
            const uint8_t* raw_k     = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_k_off);
            const uint8_t* raw_v     = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_v_off);
            const uint8_t* raw_out   = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_output_off);

            alix_rmsnorm(x, w_attn_norm, x_norm, DIM_MODEL);

            for (int r = 0; r < DIM_KV; ++r) {
                const block_q4_K_t* row_b = (const block_q4_K_t*)(raw_k + (size_t)r * ROW_BYTES_Q4K);
                k_vec[r] = dot_q4_K_row(row_b, x_norm);
            }

            int q6k = is_q6k_layer(l);
            if (q6k) {
                for (int r = 0; r < DIM_KV; ++r) {
                    const block_q6_K_t* row_b = (const block_q6_K_t*)(raw_v + (size_t)r * ROW_BYTES_Q6K);
                    v_vec[r] = dot_q6_K_row(row_b, x_norm);
                }
            } else {
                for (int r = 0; r < DIM_KV; ++r) {
                    const block_q5_K_t* row_b = (const block_q5_K_t*)(raw_v + (size_t)r * ROW_BYTES_Q5K);
                    v_vec[r] = dot_q5_K_row(row_b, x_norm);
                }
            }

            for (int r = 0; r < DIM_MODEL; ++r) {
                const block_q4_K_t* row_b = (const block_q4_K_t*)(raw_q + (size_t)r * ROW_BYTES_Q4K);
                q_vec[r] = dot_q4_K_row(row_b, x_norm);
            }

            alix_apply_rope(q_vec, NUM_HEADS, HEAD_DIM, pos, ROPE_THETA);
            alix_apply_rope(k_vec, NUM_KV_HEADS, HEAD_DIM, pos, ROPE_THETA);

            size_t kv_offset = (size_t)l * (MAX_SEQ_LEN * DIM_KV) + (size_t)pos * DIM_KV;
            memcpy(k_cache + kv_offset, k_vec, DIM_KV * sizeof(float));
            memcpy(v_cache + kv_offset, v_vec, DIM_KV * sizeof(float));

            for (int h = 0; h < NUM_HEADS; ++h) {
                int kv_h = h / GQA_GROUP;
                const float* q_head = q_vec + h * HEAD_DIM;
                float scores[MAX_SEQ_LEN];
                float max_score = -1e9f;

                for (int s = 0; s <= pos; ++s) {
                    size_t s_off = (size_t)l * (MAX_SEQ_LEN * DIM_KV) + (size_t)s * DIM_KV + kv_h * HEAD_DIM;
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
                        size_t s_off = (size_t)l * (MAX_SEQ_LEN * DIM_KV) + (size_t)s * DIM_KV + kv_h * HEAD_DIM;
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

            /* FFN Fovéa */
            const float* w_ffn_norm = (const float*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].ffn_norm_off);
            const uint8_t* raw_gate = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].ffn_gate_off);
            const uint8_t* raw_up   = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].ffn_up_off);
            const uint8_t* raw_down = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].ffn_down_off);

            alix_rmsnorm(x, w_ffn_norm, x_norm, DIM_MODEL);

            for (int k = 0; k < FOVEA_TOP; ++k) {
                int nid = FOVEA_GEO_L00[k];
                const block_q4_K_t* b_g = (const block_q4_K_t*)(raw_gate + (size_t)nid * ROW_BYTES_Q4K);
                const block_q4_K_t* b_u = (const block_q4_K_t*)(raw_up   + (size_t)nid * ROW_BYTES_Q4K);
                float dot_g = dot_q4_K_row(b_g, x_norm);
                float dot_u = dot_q4_K_row(b_u, x_norm);
                act_fovea[k] = silu(dot_g) * dot_u;
            }

            if (q6k) {
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
            } else {
                for (int r = 0; r < DIM_MODEL; ++r) {
                    const uint8_t* row_r = raw_down + (size_t)r * ROW_BYTES_DOWN_Q4K;
                    float sum_down = 0.0f;
                    for (int k = 0; k < FOVEA_TOP; ++k) {
                        int nid = FOVEA_GEO_L00[k];
                        int sb = nid / 256;
                        int idx = nid % 256;
                        const block_q4_K_t* b = (const block_q4_K_t*)(row_r + (size_t)sb * sizeof(block_q4_K_t));
                        float w = dequantize_q4_K_single(b, idx);
                        sum_down += act_fovea[k] * w;
                    }
                    x[r] += sum_down;
                }
            }

            /* Log intermédiaire sur le dernier token ':' */
            if (pos == prompt_len - 1 && (l % 8 == 0 || l >= 76)) {
                alix_rmsnorm(x, output_norm, x_norm, DIM_MODEL);
                float l_p = dot_q6_K_row(row_paris, x_norm);
                float l_m = dot_q6_K_row(row_mills, x_norm);
                float l_f = dot_q6_K_row(row_france, x_norm);
                printf("  [L%02d] logit(Paris)=%6.2f | logit(Mills)=%6.2f | logit(France)=%6.2f\n", l, l_p, l_m, l_f);
            }
        }
    }

    alix_laser_close(&file);
    return 0;
}
