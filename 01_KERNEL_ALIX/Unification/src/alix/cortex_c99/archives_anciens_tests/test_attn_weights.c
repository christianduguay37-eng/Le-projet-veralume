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
#define ROPE_THETA          500000.0f
#define EPS_RMSNORM         1e-5f

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

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    const wchar_t* usb_path = L"E:\\Modeles_4e_Etage\\Llama-3.3-70B-Instruct-Q4_K_M.gguf";
    alix_laser_file_t file;
    if (!alix_laser_open(&file, usb_path, ALIX_IO_MMAP)) {
        printf("Erreur mmap\n"); return 1;
    }

    const uint8_t* raw_embed = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_TOKEN_EMBD_OFFSET);

    float* x         = (float*)malloc(DIM_MODEL * sizeof(float));
    float* x_norm    = (float*)malloc(DIM_MODEL * sizeof(float));
    float* q_vec     = (float*)malloc(DIM_MODEL * sizeof(float));
    float* k_vec     = (float*)malloc(DIM_KV * sizeof(float));
    float* v_vec     = (float*)malloc(DIM_KV * sizeof(float));
    float* attn_out  = (float*)malloc(DIM_MODEL * sizeof(float));
    float* attn_proj = (float*)malloc(DIM_MODEL * sizeof(float));
    float* k_cache   = (float*)malloc(16 * MAX_SEQ_LEN * DIM_KV * sizeof(float));
    float* v_cache   = (float*)malloc(16 * MAX_SEQ_LEN * DIM_KV * sizeof(float));

    /* Prompt tokens:
     * 0: <|begin_of_text|>
     * 1: La
     * 2: capital
     * 3: e
     * 4: de
     * 5: la
     * 6: France
     * 7: est
     * 8: :
     */
    int prompt_tokens[] = { 128000, 8921, 6864, 68, 409, 1208, 9822, 1826, 551 };
    const char* tok_names[] = { "<bos>", "La", "capital", "e", "de", "la", "France", "est", ":" };
    int prompt_len = 9;

    printf("====================================================================\n");
    printf("  🔬 AUDIT DES POIDS D'ATTENTION AU DERNIER TOKEN ':' (pos=8)\n");
    printf("====================================================================\n\n");

    int test_layers[] = { 0, 1, 4, 8, 12, 15 };
    int n_layers = sizeof(test_layers) / sizeof(test_layers[0]);

    for (int pos = 0; pos < prompt_len; ++pos) {
        int tok = prompt_tokens[pos];
        const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_embed + (uint64_t)tok * ROW_BYTES_Q4K);
        for (int sb = 0; sb < BLOCKS_PER_ROW_8192; ++sb) dequantize_q4_K_block(&emb_row[sb], x + (sb * 256));

        for (int li = 0; li < n_layers; ++li) {
            int l = test_layers[li];
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

            int q6k = (l < 10 || l >= 70 || l % 3 == 0);
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

            size_t kv_offset = (size_t)li * (MAX_SEQ_LEN * DIM_KV) + (size_t)pos * DIM_KV;
            memcpy(k_cache + kv_offset, k_vec, DIM_KV * sizeof(float));
            memcpy(v_cache + kv_offset, v_vec, DIM_KV * sizeof(float));

            /* Affichage de l'attention moyenne des têtes au dernier token ':' */
            if (pos == prompt_len - 1) {
                float avg_attn[MAX_SEQ_LEN] = {0};
                for (int h = 0; h < NUM_HEADS; ++h) {
                    int kv_h = h / GQA_GROUP;
                    const float* q_head = q_vec + h * HEAD_DIM;
                    float scores[MAX_SEQ_LEN];
                    float max_score = -1e9f;

                    for (int s = 0; s <= pos; ++s) {
                        size_t s_off = (size_t)li * (MAX_SEQ_LEN * DIM_KV) + (size_t)s * DIM_KV + kv_h * HEAD_DIM;
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
                    for (int s = 0; s <= pos; ++s) avg_attn[s] += scores[s] * inv_sum / (float)NUM_HEADS;
                }

                printf("  [Couche L%02d] Head 0 raw scores:\n", l);
                for (int s = 0; s <= pos; ++s) {
                    size_t s_off = (size_t)li * (MAX_SEQ_LEN * DIM_KV) + (size_t)s * DIM_KV + 0 * HEAD_DIM;
                    const float* k_hist = k_cache + s_off;
                    float dot_s = 0.0f;
                    for (int d_i = 0; d_i < HEAD_DIM; ++d_i) dot_s += q_vec[d_i] * k_hist[d_i];
                    dot_s /= sqrtf((float)HEAD_DIM);
                    printf("    s=%d (%-8s) : score = %8.2f\n", s, tok_names[s], dot_s);
                }

                printf("  [Couche L%02d] Poids d'attention moyens depuis ':' :\n", l);
                for (int s = 0; s <= pos; ++s) {
                    printf("    s=%d (%-8s) : %5.1f %%\n", s, tok_names[s], avg_attn[s] * 100.0f);
                }
                printf("\n");
            }
        }
    }

    alix_laser_close(&file);
    return 0;
}
