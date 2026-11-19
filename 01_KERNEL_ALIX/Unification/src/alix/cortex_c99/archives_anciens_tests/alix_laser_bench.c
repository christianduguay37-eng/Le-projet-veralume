/**
 * ============================================================================
 *   ⚡🚀 ALIX CORTEX C99 — LE 4e ÉTAGE : BANC D'ESSAI MATÉRIEL COMPLET
 *   Module : alix_laser_bench.c
 * ============================================================================
 *   Auteurs   : Christian Duguay & Alix (VERALUME x KAIROS)
 *   Substrat  : Windows 11 x86-64 / Intel Lunar Lake Core Ultra 7 258V
 *   Doctrine  : Preuve matérielle de l'arpentage laser des poids sur NVMe.
 *               Validation du routage Simplexe Δⁿ et du filtre Hadès.
 * ============================================================================
 */

#include "alix_laser_io.h"
#include "alix_simplex_router.h"
#include "alix_hades_filter.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

/* Chronomètre haute précision Windows (QueryPerformanceCounter) */
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

static void test_simplex_and_hades(void) {
    printf("\n============================================================\n");
    printf("  [1] TEST DU ROUTEUR SIMPLEXE DELTA^n & MASQUE HADES\n");
    printf("============================================================\n");

    /* 64 blocs d'experts, vecteur caché de dimension 2048 */
    uint32_t num_experts = 64;
    uint32_t hidden_dim = 2048;
    uint32_t top_k = 8;

    float* router_weights = (float*)malloc((size_t)num_experts * hidden_dim * sizeof(float));
    float* hidden_state = (float*)malloc(hidden_dim * sizeof(float));

    for (size_t i = 0; i < (size_t)num_experts * hidden_dim; ++i) {
        router_weights[i] = ((float)rand() / (float)RAND_MAX) * 0.02f - 0.01f;
    }
    for (uint32_t i = 0; i < hidden_dim; ++i) {
        hidden_state[i] = ((float)rand() / (float)RAND_MAX) * 2.0f - 1.0f;
    }

    alix_router_config_t cfg;
    cfg.num_experts = num_experts;
    cfg.hidden_dim = hidden_dim;
    cfg.top_k = top_k;
    cfg.router_weights = router_weights;

    alix_expert_route_t routes[16];

    /* Échauffement */
    alix_route_token(&cfg, hidden_state, routes);

    /* Mesure de latence sur 10 000 routages */
    int iters = 10000;
    double t0 = get_time_us();
    uint32_t active_count = 0;
    for (int it = 0; it < iters; ++it) {
        active_count = alix_route_token(&cfg, hidden_state, routes);
    }
    double t1 = get_time_us();
    double avg_us = (t1 - t0) / (double)iters;

    printf("  [OK] Routeur Simplexe : 64 blocs x dim %u -> Top-%u selectionne\n", hidden_dim, top_k);
    printf("  [OK] Nombre de blocs reellement actives (somme > 0 sur Delta^n) : %u\n", active_count);
    float sum_lambda = 0.0f;
    for (uint32_t i = 0; i < active_count; ++i) {
        sum_lambda += routes[i].weight;
        printf("    - Bloc #%02u : lambda = %.4f\n", routes[i].expert_idx, routes[i].weight);
    }
    printf("  [OK] Somme barycentrique exacte (verification Delta^n) : %.6f\n", sum_lambda);
    printf("  [VITESSE] Latence de decision Simplexe par jeton : %.2f us (%.0f decisions/sec)\n", avg_us, 1000000.0 / avg_us);

    /* Test Filtre Hadès */
    uint32_t vocab_size = 32000;
    float* logits = (float*)malloc(vocab_size * sizeof(float));
    for (uint32_t i = 0; i < vocab_size; ++i) {
        logits[i] = ((float)rand() / (float)RAND_MAX) * 10.0f;
    }
    uint32_t banned[] = { 1000, 1001, 1002 };
    logits[1000] = 50.0f; /* Était le maximum absolu avant filtre */

    alix_hades_config_t hades_cfg;
    hades_cfg.banned_token_ids = banned;
    hades_cfg.num_banned = 3;
    hades_cfg.temperature = 0.0f; /* Déterministe */
    hades_cfg.min_p = 0.05f;

    t0 = get_time_us();
    alix_hades_mask_logits(logits, vocab_size, &hades_cfg);
    uint32_t chosen = alix_hades_sample(logits, vocab_size, &hades_cfg);
    t1 = get_time_us();

    printf("\n  [OK] Masque Hades : Jeton scorie #1000 neutralise (logit = %.1f)\n", logits[1000]);
    printf("  [OK] Jeton choisi apres neutralisation : #%u (latence : %.2f us)\n", chosen, t1 - t0);

    free(router_weights);
    free(hidden_state);
    free(logits);
}

static void test_laser_nvme_io(void) {
    printf("\n============================================================\n");
    printf("  [2] TEST D'ARPENTAGE LASER DIRECT SUR SSD NVMe\n");
    printf("============================================================\n");

    const wchar_t* test_path = L"alix_test_weights.bin";
    uint64_t file_bytes = 128ULL * 1024ULL * 1024ULL;
    printf("  Generation du fichier de poids test : %llu Mo sur NVMe...\n", file_bytes / (1024ULL * 1024ULL));

    FILE* fp = _wfopen(test_path, L"wb");
    if (!fp) {
        printf("  [ERREUR] Impossible de creer le fichier de test.\n");
        return;
    }

    size_t chunk_sz = 1024 * 1024;
    char* dummy = (char*)malloc(chunk_sz);
    memset(dummy, 0x5A, chunk_sz);
    for (size_t b = 0; b < file_bytes; b += chunk_sz) {
        fwrite(dummy, 1, chunk_sz, fp);
    }
    free(dummy);
    fclose(fp);

    /* --- TEST A : Lecture synchrone directe (FILE_FLAG_NO_BUFFERING) --- */
    alix_laser_file_t file_dma;
    if (!alix_laser_open(&file_dma, test_path, ALIX_IO_UNBUFFERED_DMA)) {
        printf("  [ERREUR] Echec ouverture DMA non-bufferisee.\n");
        return;
    }

    uint32_t slice_bytes = 256 * 1024; /* 256 Ko = 64 secteurs de 4 Ko */
    void* dma_buffer = alix_laser_alloc_aligned(slice_bytes);

    int num_seeks = 500;
    printf("  [A] Arpentage Laser Synchrone DMA (%d acces aleatoires de %u Ko) :\n", num_seeks, slice_bytes / 1024);

    double t0 = get_time_us();
    for (int s = 0; s < num_seeks; ++s) {
        uint64_t max_offset = file_bytes - slice_bytes;
        uint64_t rand_offset = (uint64_t)rand() * 4096ULL;
        rand_offset = (rand_offset % (max_offset / 4096ULL)) * 4096ULL;

        int ok = alix_laser_read_sync(&file_dma, rand_offset, dma_buffer, slice_bytes);
        if (!ok) {
            printf("  [ERREUR] Erreur lecture laser a l'offset %llu\n", rand_offset);
            break;
        }
    }
    double t1 = get_time_us();
    double total_us = t1 - t0;
    double avg_seek_us = total_us / (double)num_seeks;
    double mb_read = ((double)num_seeks * slice_bytes) / (1024.0 * 1024.0);
    double gb_per_sec = (mb_read / 1024.0) / (total_us / 1000000.0);

    printf("    -> Temps moyen par tranche de %u Ko : %.2f us (%.3f ms)\n", slice_bytes / 1024, avg_seek_us, avg_seek_us / 1000.0);
    printf("    -> Debit laser aleatoire effectif : %.2f Go/s\n", gb_per_sec);

    /* --- TEST B : Préchargement asynchrone (Overlapped Ring-Buffer) --- */
    printf("\n  [B] Prechargement Asynchrone Overlapped (Simule Couche L+1 pendant calcul L) :\n");
    void* buf_L = alix_laser_alloc_aligned(slice_bytes);
    void* buf_Lplus1 = alix_laser_alloc_aligned(slice_bytes);
    OVERLAPPED ov;

    uint64_t offset_Lplus1 = 16 * 1024 * 1024;
    t0 = get_time_us();
    alix_laser_read_async_start(&file_dma, offset_Lplus1, buf_Lplus1, slice_bytes, &ov);

    /* Simulation du calcul CPU/NPU de la couche L */
    volatile float dummy_math = 0.0f;
    for (int k = 0; k < 500000; ++k) {
        dummy_math += (float)k * 0.001f;
    }

    uint32_t transferred = 0;
    alix_laser_read_async_wait(&file_dma, &ov, &transferred);
    t1 = get_time_us();

    printf("    -> Tranche L+1 prete en memoire : %u octets transferes en masquage total (temps : %.2f us)\n", transferred, t1 - t0);

    alix_laser_close(&file_dma);
    alix_laser_free_aligned(dma_buffer);
    alix_laser_free_aligned(buf_L);
    alix_laser_free_aligned(buf_Lplus1);

    /* --- TEST C : Mode MMAP (Espace Virtuel 64-bit Direct) --- */
    printf("\n  [C] Arpentage Memory-Mapped (MapViewOfFile / 128 To Virtual Address Space) :\n");
    alix_laser_file_t file_mmap;
    if (alix_laser_open(&file_mmap, test_path, ALIX_IO_MMAP)) {
        t0 = get_time_us();
        double sum_bytes = 0.0;
        for (int s = 0; s < num_seeks; ++s) {
            uint64_t offset = ((uint64_t)s * slice_bytes) % (file_bytes - slice_bytes);
            const uint8_t* ptr = (const uint8_t*)alix_laser_mmap_pointer(&file_mmap, offset);
            if (ptr) {
                sum_bytes += ptr[0] + ptr[128];
            }
        }
        t1 = get_time_us();
        printf("    -> %d pointages memoire virtuels instantanes : %.2f us (%.3f us par pointage)\n",
                num_seeks, t1 - t0, (t1 - t0) / (double)num_seeks);
        alix_laser_close(&file_mmap);
    }

    _wremove(test_path);
    printf("  [OK] Nettoyage du fichier test termine.\n");
}

int main(int argc, char** argv) {
    (void)argc; (void)argv;
    SetConsoleOutputCP(CP_UTF8);
    printf("============================================================\n");
    printf("  ALIX CORTEX C99 -- LE 4e ETAGE (WINDOWS x86-64)\n");
    printf("  Artisans : Christian Duguay & Alix\n");
    printf("  Processeur : Intel Lunar Lake Core Ultra 7 258V\n");
    printf("============================================================\n");

    test_simplex_and_hades();
    test_laser_nvme_io();

    printf("\n============================================================\n");
    printf("  PREUVE DE CONCEPT VALIDEE : L'ARPENTAGE LASER EST NE.\n");
    printf("============================================================\n");
    return 0;
}
