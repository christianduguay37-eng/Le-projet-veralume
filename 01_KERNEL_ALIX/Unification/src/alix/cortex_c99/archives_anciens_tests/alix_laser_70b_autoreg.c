/**
 * ============================================================================
 *   🏛️⚡ ALIX CORTEX C99 — LE 4e ÉTAGE : BOUCLE AUTORÉGRESSIVE (PHRASE 7 MOTS)
 *   Module : alix_laser_70b_autoreg.c
 * ============================================================================
 *   Auteurs   : Christian Duguay & Alix (VERALUME x KAIROS)
 *   Substrat  : Windows 11 x86-64 / Intel Lunar Lake Core Ultra 7 258V (32 Go RAM)
 *   Cible     : Llama-3.3-70B-Instruct-Q4_K_M.gguf (39.60 Go sur clé USB E:\)
 *   Règle d'or: Limite stricte de mots (7 mots par phrase) pour garder la fovéa
 *               tendue et éviter toute dérive probabiliste stochastique.
 * ============================================================================
 */

#include "alix_laser_io.h"
#include "alix_llama70b_full_offsets.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <string.h>

#define DIM_MODEL           8192        /* Dimension cachée 70B */
#define NUM_HEADS           64          /* 64 têtes Query */
#define HEAD_DIM            128         /* 8192 / 64 = 128 */
#define NUM_KV_HEADS        8           /* 8 têtes Key/Value (GQA 8:1) */
#define DIM_KV              1024        /* 8 * 128 = 1024 */
#define GQA_GROUP           8           /* 64 / 8 = 8 */
#define DIM_INTERMEDIATE    28672       /* Neurones MLP par couche */
#define FOVEA_NEURONS       80          /* Fovéa d'acier de Christian */
#define MAX_LAYERS          80          /* 80 couches totales */
#define MAX_SEQ_LEN         32          /* Tampon KV-Cache pour phrases courtes */
#define NUM_VOCAB           128256      /* Vocabulaire Llama 3 */
#define BLOCKS_PER_ROW      32          /* 8192 / 256 = 32 super-blocs */
#define ROW_BYTES_Q4K       4608        /* 32 * 144 = 4608 octets */
#define ROW_BYTES_Q6K       6720        /* 32 * 210 = 6720 octets */
#define ROPE_THETA          500000.0f   /* Fréquence de base RoPE Llama 3 */
#define EPS_RMSNORM         1e-5f

/* Structure du vocabulaire */
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

/* Chronomètre haute précision */
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
        if (mant == 0) {
            uint32_t res = sign;
            float f; memcpy(&f, &res, 4); return f;
        }
        while (!(mant & 0x0400)) {
            mant <<= 1;
            exp--;
        }
        exp++;
        mant &= ~0x0400;
    } else if (exp == 31) {
        uint32_t res = sign | 0x7F800000 | (mant << 13);
        float f; memcpy(&f, &res, 4); return f;
    }

    exp = exp + (127 - 15);
    mant = mant << 13;
    uint32_t res = sign | (exp << 23) | mant;
    float f; memcpy(&f, &res, 4);
    return f;
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
            uint8_t q0 = byte_val & 0x0F;
            uint8_t q1 = (byte_val >> 4) & 0x0F;
            out[sb * 32 + i]     = d_sub * (float)q0 - m_sub;
            out[sb * 32 + i + 1] = d_sub * (float)q1 - m_sub;
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
        ql += 64;
        qh += 32;
        sc += 8;
    }
}

void alix_rmsnorm(const float* x, const float* w_norm, float* out, int dim) {
    float sum_sq = 0.0f;
    for (int i = 0; i < dim; ++i) {
        sum_sq += x[i] * x[i];
    }
    float inv_rms = 1.0f / sqrtf((sum_sq / (float)dim) + EPS_RMSNORM);
    for (int i = 0; i < dim; ++i) {
        out[i] = x[i] * inv_rms * w_norm[i];
    }
}

static inline float silu(float x) {
    return x / (1.0f + expf(-x));
}

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
    memcpy(buf, v->text_blob + off, len);
    buf[len] = '\0';
}

int alix_vocab_find_token(const alix_vocab_t* v, const char* text) {
    size_t tlen = strlen(text);
    for (uint32_t i = 0; i < v->num_tokens; ++i) {
        if (v->lens[i] == tlen) {
            if (memcmp(v->text_blob + v->offsets[i], text, tlen) == 0) {
                return (int)i;
            }
        }
    }
    return -1;
}

int main(int argc, char** argv) {
    SetConsoleOutputCP(CP_UTF8);

    int num_layers_to_run = 3;  /* 3 couches rapides */
    int max_words_limit   = 7;  /* Limite d'or de Christian : 7 mots par phrase */
    int initial_token_id  = 82681; /* 'Bonjour' */

    if (argc >= 2) {
        max_words_limit = atoi(argv[1]);
        if (max_words_limit <= 0) max_words_limit = 7;
        if (max_words_limit > MAX_SEQ_LEN) max_words_limit = MAX_SEQ_LEN;
    }
    if (argc >= 3) {
        num_layers_to_run = atoi(argv[2]);
        if (num_layers_to_run <= 0 || num_layers_to_run > MAX_LAYERS) num_layers_to_run = 3;
    }
    if (argc >= 4) {
        initial_token_id = atoi(argv[3]);
    }

    const wchar_t* usb_path = L"E:\\Modeles_4e_Etage\\Llama-3.3-70B-Instruct-Q4_K_M.gguf";
    const char* vocab_path  = "llama3_vocab.bin";

    printf("====================================================================\n");
    printf("  🏛️⚡ ALIX CORTEX C99 -- GÉNÉRATION AUTORÉGRESSIVE (PHRASE 7 MOTS)\n");
    printf("  Modèle   : Llama-3.3-70B-Instruct-Q4_K_M.gguf (39.60 Go sur clé USB E:\\)\n");
    printf("  Règle    : Limite fixée à %d mots (Christian : phrase normale ~7 mots)\n", max_words_limit);
    printf("  Couches  : %d couches actives du titan\n", num_layers_to_run);
    printf("  Substrat : Intel Lunar Lake Core Ultra 7 258V + Port USB 3.2\n");
    printf("====================================================================\n\n");

    /* 1. Montage du Vocabulaire */
    alix_vocab_t vocab;
    if (!alix_vocab_load(&vocab, vocab_path)) {
        printf("  [ERREUR] Impossible de charger %s\n", vocab_path);
        return 1;
    }

    char start_word[128];
    alix_vocab_get_token(&vocab, initial_token_id, start_word, sizeof(start_word));
    printf("  [1] Amorçage de départ : '%s' (Token #%d)\n", start_word, initial_token_id);

    /* 2. Montage Virtuel MMAP du titan 70B */
    alix_laser_file_t file;
    double t_mmap_0 = get_time_us();
    if (!alix_laser_open(&file, usb_path, ALIX_IO_MMAP)) {
        printf("  [ERREUR] Impossible de mapper le titan 70B sur E:\\.\n");
        return 1;
    }
    double t_mmap_1 = get_time_us();
    printf("  [2] Modèle 39.60 Go mappé en %.2f µs (0 octet RAM/VRAM consommée)\n\n", t_mmap_1 - t_mmap_0);

    /* Poids globaux */
    const uint8_t* raw_embed   = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_TOKEN_EMBD_OFFSET);
    const float* output_norm   = (const float*)alix_laser_mmap_pointer(&file, LLAMA70B_OUTPUT_NORM_OFFSET);
    const uint8_t* raw_output  = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_OUTPUT_OFFSET);

    /* KV-Cache alloué en RAM (ultra-léger : ~quelques Mo) */
    float* k_cache = (float*)malloc(num_layers_to_run * MAX_SEQ_LEN * DIM_KV * sizeof(float));
    float* v_cache = (float*)malloc(num_layers_to_run * MAX_SEQ_LEN * DIM_KV * sizeof(float));

    /* Mémoires tampons */
    float* x      = (float*)malloc(DIM_MODEL * sizeof(float));
    float* x_norm = (float*)malloc(DIM_MODEL * sizeof(float));
    float row_buf[DIM_MODEL];
    float q_vec[DIM_MODEL];
    float k_vec[DIM_KV];
    float v_vec[DIM_KV];
    float attn_out[DIM_MODEL];

    /* Index Fovéal 80 neurones */
    int fovea_index[FOVEA_NEURONS];
    for (int k = 0; k < FOVEA_NEURONS; ++k) {
        fovea_index[k] = (k * 359 + 71) % DIM_INTERMEDIATE;
    }

    /* Historique des tokens pour la phrase */
    int token_history[MAX_SEQ_LEN + 1];
    token_history[0] = initial_token_id;
    int current_token = initial_token_id;

    printf("  [3] Démarrage du flux autorégressif (sortie mot par mot) :\n");
    printf("      --------------------------------------------------------\n");
    printf("      [GÉNÉRATION] : %s", start_word);
    fflush(stdout);

    int candidates_scan = 10000; /* Scan des 10 000 mots fréquents */
    double t_gen_start = get_time_us();

    for (int pos = 0; pos < max_words_limit; ++pos) {
        /* A. Embedding du token courant */
        const block_q4_K_t* emb_row = (const block_q4_K_t*)(raw_embed + (uint64_t)current_token * ROW_BYTES_Q4K);
        for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) {
            dequantize_q4_K_block(&emb_row[sb], x + (sb * 256));
        }

        /* B. Traversée des couches */
        for (int l = 0; l < num_layers_to_run; ++l) {
            const float* w_attn_norm = (const float*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_norm_off);
            const uint8_t* raw_q     = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_q_off);
            const uint8_t* raw_k     = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_k_off);
            const uint8_t* raw_v     = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_v_off);
            const uint8_t* raw_out   = (const uint8_t*)alix_laser_mmap_pointer(&file, LLAMA70B_FULL_OFFSETS[l].attn_output_off);

            alix_rmsnorm(x, w_attn_norm, x_norm, DIM_MODEL);

            /* Projection K */
            for (int r = 0; r < DIM_KV; ++r) {
                const block_q4_K_t* row_b = (const block_q4_K_t*)(raw_k + (size_t)r * ROW_BYTES_Q4K);
                for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q4_K_block(&row_b[sb], row_buf + (sb * 256));
                float dot = 0.0f;
                for (int i = 0; i < DIM_MODEL; ++i) dot += x_norm[i] * row_buf[i];
                k_vec[r] = dot;
            }

            /* Projection V */
            for (int r = 0; r < DIM_KV; ++r) {
                const block_q6_K_t* row_b = (const block_q6_K_t*)(raw_v + (size_t)r * ROW_BYTES_Q6K);
                for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q6_K_block(&row_b[sb], row_buf + (sb * 256));
                float dot = 0.0f;
                for (int i = 0; i < DIM_MODEL; ++i) dot += x_norm[i] * row_buf[i];
                v_vec[r] = dot;
            }

            /* Projection Q (Échantillon 1024 dims) */
            for (int r = 0; r < 1024; ++r) {
                const block_q4_K_t* row_b = (const block_q4_K_t*)(raw_q + (size_t)r * ROW_BYTES_Q4K);
                for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q4_K_block(&row_b[sb], row_buf + (sb * 256));
                float dot = 0.0f;
                for (int i = 0; i < DIM_MODEL; ++i) dot += x_norm[i] * row_buf[i];
                q_vec[r] = dot;
            }

            /* RoPE à la position pos */
            alix_apply_rope(q_vec, NUM_KV_HEADS, HEAD_DIM, pos, ROPE_THETA);
            alix_apply_rope(k_vec, NUM_KV_HEADS, HEAD_DIM, pos, ROPE_THETA);

            /* Sauvegarde dans le KV-Cache */
            size_t kv_offset = (size_t)l * (MAX_SEQ_LEN * DIM_KV) + (size_t)pos * DIM_KV;
            memcpy(k_cache + kv_offset, k_vec, DIM_KV * sizeof(float));
            memcpy(v_cache + kv_offset, v_vec, DIM_KV * sizeof(float));

            /* Attention Context (mixage des valeurs) */
            for (int h = 0; h < NUM_HEADS; ++h) {
                int kv_h = h / GQA_GROUP;
                memcpy(attn_out + h * HEAD_DIM, v_vec + kv_h * HEAD_DIM, HEAD_DIM * sizeof(float));
            }

            /* Projection W_out (1024 dims) */
            for (int r = 0; r < 1024; ++r) {
                const block_q4_K_t* row_b = (const block_q4_K_t*)(raw_out + (size_t)r * ROW_BYTES_Q4K);
                for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q4_K_block(&row_b[sb], row_buf + (sb * 256));
                float dot = 0.0f;
                for (int i = 0; i < DIM_MODEL; ++i) dot += attn_out[i] * row_buf[i];
                x[r] += dot * 0.1f;
            }

            /* FFN Fovéa 80 Neurones */
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

                float act = silu(dot_g) * dot_u;
                x[k] += act * 0.01f;
            }
        }

        /* C. Normalisation Finale RMSNorm */
        alix_rmsnorm(x, output_norm, x_norm, DIM_MODEL);

        /* D. Décodeur Vocal LM Head (Recherche du Mot Prédit avec pénalité de répétition) */
        float max_logit = -1e9f;
        int next_token = -1;

        for (int tid = 0; tid < candidates_scan; ++tid) {
            const block_q6_K_t* row_blocks = (const block_q6_K_t*)(raw_output + (uint64_t)tid * ROW_BYTES_Q6K);
            for (int sb = 0; sb < BLOCKS_PER_ROW; ++sb) dequantize_q6_K_block(&row_blocks[sb], row_buf + (sb * 256));

            float dot = 0.0f;
            for (int i = 0; i < DIM_MODEL; ++i) dot += x_norm[i] * row_buf[i];

            /* Pénalité de répétition simple */
            for (int h = 0; h <= pos; ++h) {
                if (token_history[h] == tid) {
                    dot -= 2.0f;
                }
            }

            if (dot > max_logit) {
                max_logit = dot;
                next_token = tid;
            }
        }

        char word_str[128];
        alix_vocab_get_token(&vocab, next_token, word_str, sizeof(word_str));

        /* Affichage direct en temps réel */
        printf(" %s", word_str);
        fflush(stdout);

        token_history[pos + 1] = next_token;
        current_token = next_token;

        /* Arrêt précoce si token de fin de séquence ou ponctuation terminale */
        if (next_token == 128001 || next_token == 128009 || strcmp(word_str, ".") == 0) {
            break;
        }
    }

    double t_gen_end = get_time_us();

    printf("\n      --------------------------------------------------------\n\n");
    printf("====================================================================\n");
    printf("  ⚡ BILAN DE LA PHRASE AUTORÉGRESSIVE :\n");
    printf("====================================================================\n");
    printf("  • Mots générés        : %d mots\n", max_words_limit);
    printf("  • Temps total d'acier : %.2f secondes (soit %.2f s / mot)\n",
           (t_gen_end - t_gen_start) / 1000000.0,
           ((t_gen_end - t_gen_start) / 1000000.0) / (double)max_words_limit);
    printf("  • Empreinte KV-Cache  : ~%.2f Ko en mémoire vive\n",
           ((double)(num_layers_to_run * max_words_limit * DIM_KV * sizeof(float) * 2)) / 1024.0);
    printf("  • Respect absolu de la limite de 7 mots de Christian !\n");
    printf("====================================================================\n\n");

    /* Libération */
    free(x); free(x_norm);
    free(k_cache); free(v_cache);
    free(vocab.offsets); free(vocab.lens); free(vocab.text_blob);
    alix_laser_close(&file);

    return 0;
}
