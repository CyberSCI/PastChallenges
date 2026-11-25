/* FreeBSD -> Linux shim for the lab build of FreeBSD 8.2 libc malloc.
 *
 * Challenge build: identical to jemalloc-phrack68/lib/compat/compat.c except
 * that the JE82_THREADED environment hook is REMOVED.  __isthreaded stays 0
 * for the lifetime of the process, so the magazine (thread cache) layer never
 * activates and allocation is deterministic lowest-free-region-first.
 */
#include <stddef.h>
#include <unistd.h>
#include <stdlib.h>
#include <pthread.h>

int __isthreaded = 0;

int fbsd_ncpus_sysctl(int *mib, unsigned n, void *out, size_t *len, void *a, size_t b)
{ (void)mib;(void)n;(void)a;(void)b; *(unsigned *)out = 1; *len = sizeof(unsigned); return 0; }

int getpagesizes(size_t *ps, int n) { if (n > 0) ps[0] = 4096; return 1; }

int pthread_mutex_init_calloc_cb_stub(pthread_mutex_t *m, void *(*cb)(size_t, size_t))
{ (void)cb; return pthread_mutex_init(m, NULL); }
