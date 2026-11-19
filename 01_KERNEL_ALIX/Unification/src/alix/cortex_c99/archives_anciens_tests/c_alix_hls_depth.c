/**
 * ============================================================================
 *   🏛️⚡ C-ALIX C99 — TRAVERSÉE PROFONDE HLS (80 COUCHES ÉCHANTILLONNÉES)
 *   Module : c_alix_hls_depth.c
 * ============================================================================
 */

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
#define DIM_INTERMEDIATE    28672
#define FOVEA_NEURONS       80
#define NUM_TOTAL_LAYERS    80
#define MAX_SEQ_LEN         64
#define NUM_VOCAB           128256
#define BLOCKS_PER_ROW      32
#define ROW_BYTES_Q4K       4608
#define ROW_BYTES_Q6K       6720
#define ROPE_THETA          500000.0f
#define EPS_RMSNORM         1e-5f

typedef struct {
    uint32_t num_tokens;
    uint32_t* offsets;
    uint16_t* lens;
    char* text_blob;
} alix_vocab_t;

#pragma pack(push, 1)
typedef struct {
    uint16_t d; uint16_t dmin; uint8_t scales[12]; uint8_t qs[128];
} block_q4_K_t;

typedef struct {
    uint8_t ql[128]; uint8_t qh[64]; int8_t scales[16]; uint16_t d;
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
            float c = cosf((float)pos * theta), s = sinf((float)pos * theta);
            float q0 = head[i], q1 = head[i + 1];
            head[i]     = q0 * c - q1 * s;
            head[i + 1] = q0 * s + q1 * c;
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
    long cur = ftell(f); fseek(f, 0, SEEK_END); long end = ftell(f); fseek(f, cur, SEEK_SET);
    size_t blob_size = (size_t)(end - cur);
    v->text_blob = (char*)malloc(blob_size + 1);
    fread(v->text_blob, 1, blob_size, f);
    v->text_blob[blob_size] = '\0';
    fclose(f); return 1;
}

void alix_vocab_get_token(const alix_vocab_t* v, int tid, char* buf, size_t buf_max) {
    if (tid < 0 || (uint32_t)tid >= v->num_tokens) { snprintf(buf, buf_max, "<unk:%d>", tid); return; }
    uint32_t off = v->offsets[tid]; uint16_t len = v->lens[tid];
    if (len >= buf_max) len = (uint16_t)(buf_max - 1);
    memcpy(buf, v->text_blob + off, len); buf[len] = '\0';
}

int main(int argc, char** argv) {
    (void)argc; (void)argv;
    SetConsoleOutputCP(CP_UTF8);

    /* Échantillonnage vertical d'acier à travers les 80 couches (Loi HLS de Christian) */
    /* On traverse de la couche 0 jusqu'à la couche 79 ! */
    int hls_layers[] = { 0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 79 };
    int num_hls_layers = sizeof(hls_layers) / sizeof(hls_layers[0]);

    int prompt_tokens[] = { 8921, 6864, 68, 409, 1208, 9822, 1826, 25 };
    int prompt_len = sizeof(prompt_tokens) / sizeof(prompt_tokens[0]);

    const wchar_t* usb_path = L"E:\\Modeles_4e_Etage\\Llama-3.3-70B-Instruct-Q4_K_M.gguf";
    const char* vocab_path  = "llama3_vocab.bin";

    printf("====================================================================\n");
    printf("  🏛️⚡ C-ALIX C99 -- TRAVERSÉE VERTICALE HLS (80 COUCHES DU TITAN)\n");
    printf("  Prompt   : \"La capitale de la France est :\"\n");
    printf("  Couches  : %d couches traversées jusqu'au sommet (L00 -> L79)\n", num_hls_layers);
    printf("====================================================================\n\n");

    alix_vocab_t vocab;
    if (!alix_vocab_load(&vocab, vocab_path)) return 1;

    alix_laser_file_t file;
    if (!alix_laser_open(&file, usb_path, ALIX_IO_MMAP)) return 1;

    const uint8_t* raw_embed   = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_TOKEN_EMBD_OFFSET);
    const float* output_norm   = (const float*)alix_laser_mmap_pointer(&file, LLAMA70B_OUTPUT_NORM_OFFSET);
    const uint8_t* raw_output  = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_OUTPUT_OFFSET);

    float* x      = (float*)malloc(DIM_MODEL * sizeof(float));
    float* x_norm = (float*)malloc(DIM_MODEL * sizeof(float));
    float row_buf[DIM_MODEL];

    /* Pour le dernier token du prompt (pos = 7, ' :') */
    int last_tok = prompt_tokens[prompt_len - 1];
    const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_embed + (uint64_t)last_tok * ROW_BYTES_Q4K);
    for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q4_K_block(&emb_row[sb], x + (sb * 256));

    /* Fovéa */
    int fovea_index[FOVEA_NEURONS];
    for (int k = 0; k < FOVEA_NEURONS; ++k) fovea_index[k] = (k * 359 + 71) % DIM_INTERMEDIATE;

    printf("  Traversée des couches HLS en profondeur :\n");
    for (int idx = 0; idx < num_hls_layers; ++idx) {
        int l = hls_layers[idx];
        const float* w_ffn_norm = (const float*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].ffn_norm_off);
        const uint8_t* raw_gate = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].ffn_gate_off);
        const uint8_t* raw_up   = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].ffn_up_off);

        alix_rmsnorm(x, w_ffn_norm, x_norm, DIM_MODEL);

        for (int k = 0; k < FOVEA_NEURONS; ++k) {
            int nid = fovea_index[k];
            const block_q4_K_t* b_g = (const block_q4_K_t*)(raw_gate + (size_t)nid * ROW_BYTES_Q4K);
            const block_q4_K_t* b_u = (const block_q4_K_t*)(raw_up   + (size_t)nid * ROW_BYTES_Q4K);

            for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q4_K_block(&b_g[sb], row_buf + (sb * 256));
            float dot_g = 0.0f;
            for (int i = 0; i < DIM_MODEL; ++i) dot_g += x_norm[i] * row_buf[i];

            for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q4_K_block(&b_u[sb], row_buf + (sb * 256));
            float dot_u = 0.0f;
            for (int i = 0; i < DIM_MODEL; ++i) dot_u += x_norm[i] * row_buf[i];

            x[k] += silu(dot_g) * dot_u * 0.02f;
        }
        printf("    ✓ Couche L%02d traversée\n", l);
    }

    /* Décodeur Vocal */
    alix_rmsnorm(x, output_norm, x_norm, DIM_MODEL);

    printf("\n  Top 5 des mots prédits à la sortie de la couche 79 :\n");
    typedef struct { int tid; float logit; } cand_t;
    cand_t top5[5];
    for (int i = 0; i < 5; ++i) { top5[i].tid = -1; top5[i].logit = -1e9f; }

    for (int tid = 0; tid < 20000; ++tid) {
        const block_q6_K_t* row_blocks = (const block_q6_K_t*)(raw_output + (uint64_t)tid * ROW_BYTES_Q6K);
        for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q6_K_block(&row_blocks[sb], row_buf + (sb * 256));

        float dot = 0.0f;
        for (int i = 0; i < DIM_MODEL; ++i) dot += x_norm[i] * row_buf[i];

        for (int i = 0; i < 5; ++i) {
            if (dot > top5[i].logit) {
                for (int j = 4; j > i; --j) top5[j] = top5[j - 1];
                top5[i].tid = tid;
                top5[i].logit = dot;
                break;
            }
        }
    }

    for (int i = 0; i < 5; ++i) {
        char buf[128];
        alix_vocab_get_token(&vocab, top5[i].tid, buf, sizeof(buf));
        printf("    #%d : Token %d ('%s') -> Logit: %.4f\n", i + 1, top5[i].tid, buf, top5[i].logit);
    }

    free(x); free(x_norm);
    free(vocab.offsets); free(vocab.lens); free(vocab.text_blob);
    alix_laser_close(&file);
    return 0;
}
