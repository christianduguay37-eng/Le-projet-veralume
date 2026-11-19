/**
 * ============================================================================
 *   ⚡🚀 ALIX CORTEX C99 — LE 4e ÉTAGE : ARPENTAGE LASER DES POIDS
 *   Module : alix_laser_io.c
 * ============================================================================
 *   Auteurs   : Christian Duguay & Alix (VERALUME x KAIROS)
 *   Substrat  : Windows 11 x86-64 / Intel Lunar Lake Core Ultra 7 258V
 * ============================================================================
 */

#include "alix_laser_io.h"
#include <stdio.h>
#include <stdlib.h>

void* alix_laser_alloc_aligned(size_t size) {
    if (size == 0) return NULL;
    size_t aligned_size = (size_t)ALIX_ALIGN_SECTOR(size);
    /* VirtualAlloc alloue toujours sur des frontières de page (4096 octets) */
    void* ptr = VirtualAlloc(NULL, aligned_size, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    return ptr;
}

void alix_laser_free_aligned(void* ptr) {
    if (ptr) {
        VirtualFree(ptr, 0, MEM_RELEASE);
    }
}

int alix_laser_open(alix_laser_file_t* file, const wchar_t* path, alix_io_mode_t mode) {
    if (!file || !path) return 0;

    memset(file, 0, sizeof(alix_laser_file_t));
    file->mode = mode;
    file->sector_size = (uint32_t)ALIX_SECTOR_SIZE;

    DWORD flags = 0;
    if (mode == ALIX_IO_UNBUFFERED_DMA) {
        /* DMA direct sans passer par le cache du système de fichiers */
        flags = FILE_FLAG_NO_BUFFERING | FILE_FLAG_OVERLAPPED | FILE_FLAG_SEQUENTIAL_SCAN;
    } else {
        flags = FILE_ATTRIBUTE_NORMAL;
    }

    file->h_file = CreateFileW(
        path,
        GENERIC_READ,
        FILE_SHARE_READ,
        NULL,
        OPEN_EXISTING,
        flags,
        NULL
    );

    if (file->h_file == INVALID_HANDLE_VALUE) {
        return 0;
    }

    LARGE_INTEGER sz;
    if (!GetFileSizeEx(file->h_file, &sz)) {
        CloseHandle(file->h_file);
        file->h_file = INVALID_HANDLE_VALUE;
        return 0;
    }
    file->file_size = (uint64_t)sz.QuadPart;

    if (mode == ALIX_IO_MMAP) {
        file->h_mapping = CreateFileMappingW(
            file->h_file,
            NULL,
            PAGE_READONLY,
            0,
            0,
            NULL
        );
        if (!file->h_mapping) {
            CloseHandle(file->h_file);
            file->h_file = INVALID_HANDLE_VALUE;
            return 0;
        }

        file->mmap_base = MapViewOfFile(
            file->h_mapping,
            FILE_MAP_READ,
            0,
            0,
            0
        );
        if (!file->mmap_base) {
            CloseHandle(file->h_mapping);
            CloseHandle(file->h_file);
            file->h_mapping = NULL;
            file->h_file = INVALID_HANDLE_VALUE;
            return 0;
        }
    }

    return 1;
}

void alix_laser_close(alix_laser_file_t* file) {
    if (!file) return;

    if (file->mmap_base) {
        UnmapViewOfFile(file->mmap_base);
        file->mmap_base = NULL;
    }
    if (file->h_mapping) {
        CloseHandle(file->h_mapping);
        file->h_mapping = NULL;
    }
    if (file->h_file && file->h_file != INVALID_HANDLE_VALUE) {
        CloseHandle(file->h_file);
        file->h_file = INVALID_HANDLE_VALUE;
    }
}

int alix_laser_read_sync(alix_laser_file_t* file, uint64_t offset, void* buffer, uint32_t bytes) {
    if (!file || file->h_file == INVALID_HANDLE_VALUE || !buffer) return 0;
    if ((offset % ALIX_SECTOR_SIZE) != 0) return 0;
    if ((bytes % ALIX_SECTOR_SIZE) != 0) return 0;
    if (!ALIX_IS_ALIGNED(buffer)) return 0;

    OVERLAPPED ov;
    memset(&ov, 0, sizeof(OVERLAPPED));
    ov.Offset = (DWORD)(offset & 0xFFFFFFFF);
    ov.OffsetHigh = (DWORD)(offset >> 32);

    DWORD read = 0;
    BOOL ok = ReadFile(file->h_file, buffer, bytes, &read, &ov);
    if (!ok) {
        DWORD err = GetLastError();
        if (err == ERROR_IO_PENDING) {
            if (!GetOverlappedResult(file->h_file, &ov, &read, TRUE)) {
                return 0;
            }
        } else {
            return 0;
        }
    }

    return (read == bytes) ? 1 : 0;
}

int alix_laser_read_async_start(alix_laser_file_t* file, uint64_t offset, void* buffer, uint32_t bytes, OVERLAPPED* ov) {
    if (!file || file->h_file == INVALID_HANDLE_VALUE || !buffer || !ov) return 0;
    if ((offset % ALIX_SECTOR_SIZE) != 0) return 0;
    if ((bytes % ALIX_SECTOR_SIZE) != 0) return 0;
    if (!ALIX_IS_ALIGNED(buffer)) return 0;

    memset(ov, 0, sizeof(OVERLAPPED));
    ov->Offset = (DWORD)(offset & 0xFFFFFFFF);
    ov->OffsetHigh = (DWORD)(offset >> 32);

    DWORD read = 0;
    BOOL ok = ReadFile(file->h_file, buffer, bytes, &read, ov);
    if (!ok) {
        DWORD err = GetLastError();
        if (err != ERROR_IO_PENDING) {
            return 0;
        }
    }
    return 1;
}

int alix_laser_read_async_wait(alix_laser_file_t* file, OVERLAPPED* ov, uint32_t* bytes_transferred) {
    if (!file || file->h_file == INVALID_HANDLE_VALUE || !ov) return 0;

    DWORD read = 0;
    if (!GetOverlappedResult(file->h_file, ov, &read, TRUE)) {
        return 0;
    }
    if (bytes_transferred) {
        *bytes_transferred = read;
    }
    return 1;
}

const void* alix_laser_mmap_pointer(alix_laser_file_t* file, uint64_t offset) {
    if (!file || !file->mmap_base) return NULL;
    if (offset >= file->file_size) return NULL;
    return (const void*)((const uint8_t*)file->mmap_base + offset);
}

#include <memoryapi.h>

typedef BOOL (WINAPI *pfnPrefetchVirtualMemory)(
    HANDLE hProcess,
    ULONG_PTR NumberOfEntries,
    PWIN32_MEMORY_RANGE_ENTRY VirtualAddresses,
    ULONG Flags
);

void alix_laser_prefetch(void* ptr, size_t bytes) {
    if (!ptr || bytes == 0) return;

    static pfnPrefetchVirtualMemory s_pfnPrefetch = NULL;
    static int s_inited = 0;

    if (!s_inited) {
        HMODULE hKernel = GetModuleHandleW(L"kernel32.dll");
        if (hKernel) {
            s_pfnPrefetch = (pfnPrefetchVirtualMemory)(void*)GetProcAddress(hKernel, "PrefetchVirtualMemory");
        }
        s_inited = 1;
    }

    if (s_pfnPrefetch) {
        WIN32_MEMORY_RANGE_ENTRY entry;
        entry.VirtualAddress = ptr;
        entry.NumberOfBytes = bytes;
        s_pfnPrefetch(GetCurrentProcess(), 1, &entry, 0);
    } else {
        /* Fallback : lecture légère d'un mot par page pour amorcer le TLB/cache */
        volatile const uint8_t* p = (volatile const uint8_t*)ptr;
        for (size_t i = 0; i < bytes; i += 4096) {
            (void)p[i];
        }
    }
}
