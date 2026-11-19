/**
 * ============================================================================
 *   ⚡🚀 ALIX CORTEX C99 — LE 4e ÉTAGE : ARPENTAGE LASER GGUF RÉEL
 *   Module : alix_laser_gguf_scan.c
 * ============================================================================
 *   Auteurs   : Christian Duguay & Alix (VERALUME x KAIROS)
 *   Substrat  : Windows 11 x86-64 / Intel Lunar Lake Core Ultra 7 258V
 *   Cible     : test_ffn_slice.gguf (Tranche FFN Qwen2 réelle de 91.2 Mo sur NVMe)
 * ============================================================================
 */

#include "alix_laser_io.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

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

typedef struct {
    const char* name;
    uint64_t    abs_offset;
    uint32_t    size_bytes;
    const char* dtype;
    const char* dims;
} ffn_tensor_meta_t;

/* Tenseurs réels extraits de test_ffn_slice.gguf */
static ffn_tensor_meta_t G_FFN_TENSORS[] = {
    {"blk.0.ffn_norm.weight", 87074496ULL, 14336,    "F32",  "[3584]"},
    {"blk.0.ffn_gate.weight", 82945728ULL, 4128768,  "Q4_K", "[3584, 2048]"},
    {"blk.0.ffn_up.weight",   87088832ULL, 4128768,  "Q4_K", "[3584, 2048]"},
    {"blk.0.ffn_down.weight", 27250368ULL, 55695360, "Q6_K", "[18944, 3584]"}
};

#define NUM_FFN_TENSORS (sizeof(G_FFN_TENSORS) / sizeof(G_FFN_TENSORS[0]))

int main(int argc, char** argv) {
    (void)argc; (void)argv;
    SetConsoleOutputCP(CP_UTF8);

    const wchar_t* gguf_path = L"C:\\Users\\Christian\\Desktop\\Projet alix\\Alix\\test  gemini\\Personel\\Projet Alix\\test_ffn_slice.gguf";

    printf("====================================================================\n");
    printf("  ⚡🚀 ALIX CORTEX C99 -- ARPENTAGE LASER SUR TRANCHE FFN REELLE\n");
    printf("  Fichier : test_ffn_slice.gguf (Qwen2 1-Layer FFN Slice)\n");
    printf("  Substrat : Intel Lunar Lake Core Ultra 7 258V + NVMe SSD\n");
    printf("====================================================================\n\n");

    /* ====================================================================== */
    /* 1. TEST MODE DIRECT DMA (FILE_FLAG_NO_BUFFERING)                       */
    /* ====================================================================== */
    printf("[1] MODE UNBUFFERED DMA DIRECT (Contournement total du cache Windows)\n");
    printf("--------------------------------------------------------------------\n");

    alix_laser_file_t file_dma;
    if (!alix_laser_open(&file_dma, gguf_path, ALIX_IO_UNBUFFERED_DMA)) {
        printf("  [ERREUR] Impossible d'ouvrir le fichier en mode DMA.\n");
        return 1;
    }
    printf("  Fichier ouvert avec succes : %llu octets (%.2f Mo)\n\n",
           file_dma.file_size, (double)file_dma.file_size / (1024.0 * 1024.0));

    /* Buffer temporaire pour les lectures alignees */
    size_t max_buf_sz = 64 * 1024 * 1024; /* 64 Mo aligne */
    void* dma_buf = alix_laser_alloc_aligned(max_buf_sz);

    double total_dma_bytes = 0.0;
    double total_dma_time_us = 0.0;

    for (size_t i = 0; i < NUM_FFN_TENSORS; ++i) {
        ffn_tensor_meta_t* tm = &G_FFN_TENSORS[i];

        uint64_t target_offset = tm->abs_offset;
        uint32_t target_bytes = tm->size_bytes;

        /* Alignement sur secteur 4096 octets */
        uint64_t aligned_offset = (target_offset / ALIX_SECTOR_SIZE) * ALIX_SECTOR_SIZE;
        uint32_t offset_delta = (uint32_t)(target_offset - aligned_offset);
        uint64_t needed_end = target_offset + target_bytes;
        uint64_t aligned_end = ALIX_ALIGN_SECTOR(needed_end);
        if (aligned_end > file_dma.file_size) {
            aligned_end = ALIX_ALIGN_SECTOR(file_dma.file_size);
        }
        uint32_t aligned_bytes = (uint32_t)(aligned_end - aligned_offset);

        /* Frappe Laser : Chronometrage direct */
        double t0 = get_time_us();
        int ok = alix_laser_read_sync(&file_dma, aligned_offset, dma_buf, aligned_bytes);
        double t1 = get_time_us();

        double elapsed_us = t1 - t0;
        double mb = (double)target_bytes / (1024.0 * 1024.0);
        double gb_sec = (mb / 1024.0) / (elapsed_us / 1000000.0);

        total_dma_bytes += target_bytes;
        total_dma_time_us += elapsed_us;

        if (ok) {
            /* Verification des premiers octets */
            const uint8_t* payload = (const uint8_t*)dma_buf + offset_delta;
            printf("  ✓ [%s] %-22s\n", tm->dtype, tm->name);
            printf("    Dimensions : %-14s | Taille : %6.1f Ko (%4.2f Mo)\n", tm->dims, (double)target_bytes/1024.0, mb);
            printf("    Offset SSD : %-10llu | Delta alignement : %u octets\n", target_offset, offset_delta);
            printf("    ⚡ Temps lecture laser : %8.2f us (%5.2f ms) | Debit : %5.2f Go/s\n", elapsed_us, elapsed_us/1000.0, gb_sec);
            printf("    Octets temoins : [0x%02X, 0x%02X, 0x%02X, 0x%02X]\n\n",
                   payload[0], payload[1], payload[2], payload[3]);
        } else {
            printf("  ❌ Echec lecture laser pour %s\n\n", tm->name);
        }
    }

    double total_dma_mb = total_dma_bytes / (1024.0 * 1024.0);
    double avg_dma_gb_sec = (total_dma_mb / 1024.0) / (total_dma_time_us / 1000000.0);
    printf("  >> BILAN FFN COMPLET (DMA DIRECT) :\n");
    printf("     Taille FFN totale lue : %.2f Mo (Norm + Gate + Up + Down)\n", total_dma_mb);
    printf("     Temps total cumule    : %.2f ms (%.2f us)\n", total_dma_time_us / 1000.0, total_dma_time_us);
    printf("     Debit moyen effectif  : %.2f Go/s\n\n", avg_dma_gb_sec);

    alix_laser_close(&file_dma);
    alix_laser_free_aligned(dma_buf);

    /* ====================================================================== */
    /* 2. TEST MODE MEMORY-MAPPED (128 To ESPACE VIRTUEL)                     */
    /* ====================================================================== */
    printf("[2] MODE MEMORY-MAPPED VIRTUEL (MapViewOfFile / Zero Copie)\n");
    printf("--------------------------------------------------------------------\n");

    alix_laser_file_t file_mmap;
    if (!alix_laser_open(&file_mmap, gguf_path, ALIX_IO_MMAP)) {
        printf("  [ERREUR] Impossible d'ouvrir en mode MMAP.\n");
        return 1;
    }

    double total_mmap_time_us = 0.0;
    for (size_t i = 0; i < NUM_FFN_TENSORS; ++i) {
        ffn_tensor_meta_t* tm = &G_FFN_TENSORS[i];

        double t0 = get_time_us();
        const void* ptr = alix_laser_mmap_pointer(&file_mmap, tm->abs_offset);
        double t1 = get_time_us();

        double elapsed_us = t1 - t0;
        total_mmap_time_us += elapsed_us;

        if (ptr) {
            const uint8_t* p = (const uint8_t*)ptr;
            printf("  ✓ [%s] %-22s -> Ptr: %p | Latence resolveur: %.3f us (%.1f ns)\n",
                   tm->dtype, tm->name, ptr, elapsed_us, elapsed_us * 1000.0);
            printf("    Octets lus : [0x%02X, 0x%02X, 0x%02X, 0x%02X]\n",
                   p[0], p[1], p[2], p[3]);
        }
    }

    printf("\n  >> BILAN MMAP :\n");
    printf("     Latence moyenne d'acquisition du pointeur : %.3f us (%.1f nanosecondes)\n\n",
           total_mmap_time_us / (double)NUM_FFN_TENSORS, (total_mmap_time_us / (double)NUM_FFN_TENSORS) * 1000.0);

    /* ====================================================================== */
    /* 3. SIMULATION PARCIMONIEUSE : LECTURE LASER D'UN BLOC DE 144 NEURONES  */
    /* ====================================================================== */
    printf("[3] TEST DE FRACTION LASER SPARSE (Bloc de 144 neurones sur Gate + Up)\n");
    printf("--------------------------------------------------------------------\n");
    /*
       Pour 144 neurones en Q4_K sur hidden_dim=3584 :
       144 * 3584 * 4.5 bits / 8 = ~289 Ko.
       Simulons la lecture d'un bloc de 289 Ko dans ffn_gate et ffn_up :
    */
    uint32_t sparse_block_bytes = (uint32_t)ALIX_ALIGN_SECTOR(289 * 1024); /* 292 Ko */
    void* sparse_buf = alix_laser_alloc_aligned(sparse_block_bytes);

    alix_laser_file_t file_sparse;
    alix_laser_open(&file_sparse, gguf_path, ALIX_IO_UNBUFFERED_DMA);

    uint64_t gate_block_offset = (G_FFN_TENSORS[1].abs_offset / ALIX_SECTOR_SIZE) * ALIX_SECTOR_SIZE;
    uint64_t up_block_offset   = (G_FFN_TENSORS[2].abs_offset / ALIX_SECTOR_SIZE) * ALIX_SECTOR_SIZE;

    double t0 = get_time_us();
    alix_laser_read_sync(&file_sparse, gate_block_offset, sparse_buf, sparse_block_bytes);
    alix_laser_read_sync(&file_sparse, up_block_offset, sparse_buf, sparse_block_bytes);
    double t1 = get_time_us();

    double sparse_elapsed_us = t1 - t0;
    double sparse_total_kb = (double)(sparse_block_bytes * 2) / 1024.0;

    printf("  ✓ Bloc sparse (144 neurones Gate + Up = %.1f Ko) :\n", sparse_total_kb);
    printf("    ⚡ Temps de frappe laser total : %.2f us (%.3f ms)\n", sparse_elapsed_us, sparse_elapsed_us / 1000.0);
    printf("    ⚡ Vitesse de rotation equivalente : %.0f blocs/seconde\n\n", 1000000.0 / sparse_elapsed_us);

    alix_laser_close(&file_sparse);
    alix_laser_free_aligned(sparse_buf);
    alix_laser_close(&file_mmap);

    printf("====================================================================\n");
    printf("  🎯 MESURES REELLES RECUEILLIES AVEC SUCCES SUR LE GGUF DU FER.\n");
    printf("====================================================================\n");

    return 0;
}
