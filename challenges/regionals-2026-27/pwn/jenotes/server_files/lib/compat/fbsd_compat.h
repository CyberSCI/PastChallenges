/* Minimal FreeBSD -> Linux shim for building FreeBSD 8.2 libc malloc.c
 * as a standalone library with je_-prefixed entry points. */
#ifndef FBSD_COMPAT_H
#define FBSD_COMPAT_H
#define _GNU_SOURCE
#define malloc              je_malloc
#define calloc              je_calloc
#define realloc             je_realloc
#define free                je_free
#define posix_memalign      je_posix_memalign
#define malloc_usable_size  je_malloc_usable_size
#define _malloc_options     je_malloc_options
#define _malloc_message     je_malloc_message
#define _malloc_thread_cleanup je_malloc_thread_cleanup
#define _malloc_prefork     je_malloc_prefork
#define _malloc_postfork    je_malloc_postfork
#include <sys/cdefs.h>
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <pthread.h>
#include <unistd.h>
#define __FBSDID(x)
#ifndef __unused
#define __unused __attribute__((unused))
#endif

#define __DECONST(type, var) ((type)(uintptr_t)(const void *)(var))
#define __weak_reference(sym, alias) /* nothing */
#define MAXPAGESIZES 1
#define CTL_HW 6
#define HW_NCPU 3
/* In FreeBSD __isthreaded flips to 1 at the first pthread_create().
 * Here it is a plain variable the demos can toggle (magazines are only
 * used when it is non-zero). */
extern int __isthreaded;
typedef struct { volatile int l; } spinlock_t;
#define _SPINLOCK_INITIALIZER {0}
#define _SPINLOCK(p)   do { while (__sync_lock_test_and_set(&(p)->l, 1)) ; } while (0)
#define _SPINUNLOCK(p) __sync_lock_release(&(p)->l)
#define _pthread_self          pthread_self
#define _pthread_mutex_lock    pthread_mutex_lock
#define _pthread_mutex_trylock pthread_mutex_trylock
#define _pthread_mutex_unlock  pthread_mutex_unlock
#define _write write
#define _pthread_mutex_init_calloc_cb pthread_mutex_init_calloc_cb_stub
#define _getprogname() "je82"
#define utrace(a, b) ((void)0)
#define issetugid() 0
int fbsd_ncpus_sysctl(int *mib, unsigned n, void *out, size_t *len, void *a, size_t b);
#define sysctl fbsd_ncpus_sysctl
int getpagesizes(size_t *ps, int n);

#define PAGE_SHIFT 12
#define PAGE_SIZE  (1UL << PAGE_SHIFT)
#define PAGE_MASK  (PAGE_SIZE - 1)
#define SIZE_T_MAX SIZE_MAX
#endif
