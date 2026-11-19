/**
 * ============================================================================
 *   ⚡🚀 ALIX CORTEX C99 — LE 4e ÉTAGE : ARPENTAGE LASER DES POIDS
 *   Module : alix_laser_io.h
 * ============================================================================
 *   Auteurs   : Christian Duguay & Alix (VERALUME x KAIROS)
 *   Substrat  : Windows 11 x86-64 / Intel Lunar Lake Core Ultra 7 258V
 *   Doctrine  : Arpentage laser direct sur NVMe SSD.
 *               Contournement total du goulot VRAM via :
 *                 1. Win32 FILE_FLAG_NO_BUFFERING + FILE_FLAG_OVERLAPPED (DMA direct)
 *                 2. Win32 CreateFileMapping / MapViewOfFile (Espace virtuel 128 To)
 *                 3. PrefetchVirtualMemory / Ring-buffer asynchrone couche L+1
 * ============================================================================
 */

#ifndef ALIX_LASER_IO_H
#define ALIX_LASER_IO_H

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define ALIX_SECTOR_SIZE        4096ULL
#define ALIX_ALIGN_SECTOR(x)    (((x) + (ALIX_SECTOR_SIZE - 1ULL)) & ~(ALIX_SECTOR_SIZE - 1ULL))
#define ALIX_IS_ALIGNED(p)      (((uintptr_t)(p) & (ALIX_SECTOR_SIZE - 1ULL)) == 0)

typedef enum {
    ALIX_IO_UNBUFFERED_DMA = 0, /* CreateFile + FILE_FLAG_NO_BUFFERING + OVERLAPPED */
    ALIX_IO_MMAP           = 1  /* CreateFileMapping + MapViewOfFile (128 To VA)   */
} alix_io_mode_t;

typedef struct {
    HANDLE          h_file;
    HANDLE          h_mapping;
    void*           mmap_base;
    uint64_t        file_size;
    alix_io_mode_t  mode;
    uint32_t        sector_size;
} alix_laser_file_t;

/**
 * Alloue un tampon mémoire aligné sur les frontières de secteur (4096 octets),
 * obligatoire pour FILE_FLAG_NO_BUFFERING.
 */
void* alix_laser_alloc_aligned(size_t size);

/**
 * Libère un tampon aligné alloué par alix_laser_alloc_aligned.
 */
void alix_laser_free_aligned(void* ptr);

/**
 * Ouvre un fichier de poids modèle (dense ou MoE) en mode direct laser.
 */
int alix_laser_open(alix_laser_file_t* file, const wchar_t* path, alix_io_mode_t mode);

/**
 * Ferme le fichier laser et libère les mappings.
 */
void alix_laser_close(alix_laser_file_t* file);

/**
 * Lecture synchrone non-bufférisée (DMA direct SSD -> RAM).
 * Offset et taille doivent être multiples de 4096 octets, et buffer aligné.
 */
int alix_laser_read_sync(alix_laser_file_t* file, uint64_t offset, void* buffer, uint32_t bytes);

/**
 * Lance une lecture asynchrone (DMA non-bloquant).
 * Permet de précharger la couche L+1 pendant que le CPU/NPU calcule la couche L.
 */
int alix_laser_read_async_start(alix_laser_file_t* file, uint64_t offset, void* buffer, uint32_t bytes, OVERLAPPED* ov);

/**
 * Attend la complétion de la lecture asynchrone.
 */
int alix_laser_read_async_wait(alix_laser_file_t* file, OVERLAPPED* ov, uint32_t* bytes_transferred);

/**
 * En mode MMAP : renvoie un pointeur direct vers la tranche de poids à l'offset donné.
 */
const void* alix_laser_mmap_pointer(alix_laser_file_t* file, uint64_t offset);

/**
 * En mode MMAP : donne un indice d'accès séquentiel / prefetch au noyau Windows
 * via PrefetchVirtualMemory (si supporté) ou lecture laser préventive.
 */
void alix_laser_prefetch(void* ptr, size_t bytes);

#ifdef __cplusplus
}
#endif

#endif /* ALIX_LASER_IO_H */
