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
#define MAX_LAYERS          12
#define MAX_SEQ_LEN         64
#define BLOCKS_PER_ROW      32
#define ROW_BYTES_Q4K       4608
#define ROW_BYTES_Q6K       6720
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

int main() {
    const wchar_t* usb_path = L"E:\\Modeles_4e_Etage\\Llama-3.3-70B-Instruct-Q4_K_M.gguf";
    alix_laser_file_t file;
    if (!alix_laser_open(&file, usb_path, ALIX_IO_MMAP)) {
        printf("Failed to open file.\n");
        return 1;
    }

    const uint8_t* raw_embed   = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_TOKEN_EMBD_OFFSET);

    float* x         = (float*)malloc(DIM_MODEL * sizeof(float));
    float* x_norm    = (float*)malloc(DIM_MODEL * sizeof(float));
    float* q_vec     = (float*)malloc(DIM_MODEL * sizeof(float));
    float* k_vec     = (float*)malloc(DIM_KV * sizeof(float));
    float* v_vec     = (float*)malloc(DIM_KV * sizeof(float));
    float* attn_out  = (float*)malloc(DIM_MODEL * sizeof(float));
    float* attn_proj = (float*)malloc(DIM_MODEL * sizeof(float));
    float* k_cache   = (float*)malloc(MAX_LAYERS * MAX_SEQ_LEN * DIM_KV * sizeof(float));
    float* v_cache   = (float*)malloc(MAX_LAYERS * MAX_SEQ_LEN * DIM_KV * sizeof(float));

    int tok = 8921; /* "La" */
    int pos = 0;
    const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_embed + (uint64_t)tok * ROW_BYTES_Q4K);
    for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q4_K_block(&emb_row[sb], x + (sb * 256));

    for (int l = 0; l <= 10; ++l) {
        printf("Starting layer %d...\n", l);
        const float* w_attn_norm = (const float*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_norm_off);
        const uint8_t* raw_q     = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_q_off);
        const uint8_t* raw_k     = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_k_off);
        const uint8_t* raw_v     = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_v_off);
        const uint8_t* raw_out   = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_output_off);

        alix_rmsnorm(x, w_attn_norm, x_norm, DIM_MODEL);
        if (isnan(x_norm[0])) { printf("  FAIL: x_norm is NaN at layer %d\n", l); break; }

        for (int r = 0; r < DIM_KV; ++r) {
            const block_q4_K_t* row_b = (const block_q4_K_t*)(raw_k + (size_t)r * ROW_BYTES_Q4K);
            k_vec[r] = dot_q4_K_row(row_b, x_norm);
        }
        if (isnan(k_vec[0])) { printf("  FAIL: k_vec is NaN at layer %d\n", l); break; }

        for (int r = 0; r < DIM_KV; ++r) {
            const block_q6_K_t* row_b = (const block_q6_K_t*)(raw_v + (size_t)r * ROW_BYTES_Q6K);
            v_vec[r] = dot_q6_K_row(row_b, x_norm);
        }
        if (isnan(v_vec[0])) { printf("  FAIL: v_vec is NaN at layer %d\n", l); break; }

        for (int r = 0; r < DIM_MODEL; ++r) {
            const block_q4_K_t* row_b = (const block_q4_K_t*)(raw_q + (size_t)r * ROW_BYTES_Q4K);
            q_vec[r] = dot_q4_K_row(row_b, x_norm);
        }
        if (isnan(q_vec[0])) { printf("  FAIL: q_vec is NaN at layer %d\n", l); break; }

        alix_apply_rope(q_vec, NUM_HEADS, HEAD_DIM, pos, ROPE_THETA);
        alix_apply_rope(k_vec, NUM_KV_HEADS, HEAD_DIM, pos, ROPE_THETA);

        for (int h = 0; h < NUM_HEADS; ++h) {
            int kv_h = h / GQA_GROUP;
            for (int d_i = 0; d_i < HEAD_DIM; ++d_i) {
                attn_out[h * HEAD_DIM + d_i] = v_vec[kv_h * HEAD_DIM + d_i];
            }
        }

        for (int r = 0; r < DIM_MODEL; ++r) {
            const block_q4_K_t* row_b = (const block_q4_K_t*)(raw_out + (size_t)r * ROW_BYTES_Q4K);
            attn_proj[r] = dot_q4_K_row(row_b, attn_out);
            x[r] += attn_proj[r] * 0.1f;
        }
        if (isnan(x[0])) { printf("  FAIL: x after attn_proj is NaN at layer %d\n", l); break; }

        const float* w_ffn_norm = (const float*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].ffn_norm_off);
        const uint8_t* raw_gate = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].ffn_gate_off);
        const uint8_t* raw_up   = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].ffn_up_off);

        alix_rmsnorm(x, w_ffn_norm, x_norm, DIM_MODEL);
        if (isnan(x_norm[0])) { printf("  FAIL: ffn_x_norm is NaN at layer %d\n", l); break; }

        for (int k = 0; k < FOVEA_TOP; ++k) {
            int nid = FOVEA_GEO_L08[k];
            const block_q4_K_t* b_g = (const block_q4_K_t*)(raw_gate + (size_t)nid * ROW_BYTES_Q4K);
            const block_q4_K_t* b_u = (const block_q4_K_t*)(raw_up   + (size_t)nid * ROW_BYTES_Q4K);
            float dot_g = dot_q4_K_row(b_g, x_norm);
            float dot_u = dot_q4_K_row(b_u, x_norm);
            float act = silu(dot_g) * dot_u;
            x[k % DIM_MODEL] += act * 0.005f;
            if (isnan(x[k % DIM_MODEL])) {
                printf("  FAIL: ffn act is NaN at layer %d k=%d nid=%d dot_g=%.2f dot_u=%.2f\n", l, k, nid, dot_g, dot_u);
                break;
            }
        }
        if (isnan(x[0])) break;
        printf("Layer %d done. x[0]=%.4f\n", l, x[0]);
    }

    alix_laser_close(&file);
    return 0;
}
