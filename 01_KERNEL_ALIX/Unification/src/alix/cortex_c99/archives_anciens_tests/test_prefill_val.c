#include "alix_laser_io.h"
#include "alix_llama70b_full_offsets.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define DIM_MODEL 8192
#define BLOCKS_PER_ROW 32
#define ROW_BYTES_Q4K 4608

#pragma pack(push, 1)
typedef struct {
    uint16_t d;
    uint16_t dmin;
    uint8_t  scales[12];
    uint8_t  qs[128];
} block_q4_K_t;
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

int main(void) {
    alix_laser_file_t file;
    if (!alix_laser_open(&file, L"E:\\Modeles_4e_Etage\\Llama-3.3-70B-Instruct-Q4_K_M.gguf", ALIX_IO_MMAP)) {
        printf("Erreur mmap\n"); return 1;
    }
    const uint8_t* raw_embed = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_TOKEN_EMBD_OFFSET);
    float x[DIM_MODEL];
    int tok = 8921; // 'La'
    const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_embed + (uint64_t)tok * ROW_BYTES_Q4K);
    for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q4_K_block(&emb_row[sb], x + (sb * 256));
    printf("x[0] = %f, x[100] = %f, isnan = %d\n", x[0], x[100], isnan(x[0]));
    alix_laser_close(&file);
    return 0;
}
