/* =====================================================================
 * jenotes - a tiny notes service without heap metadata
 * Build (see Makefile):
 *   gcc -m32 -fstack-protector-all -no-pie -fno-pie -Wl,-z,relro,-z,lazy -O0
 * ===================================================================== */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

void  *je_malloc(size_t);
void   je_free(void *);
#define malloc je_malloc
#define free   je_free

#define MAXN 40
#define NOTELEN 64

struct note {
    char           name[56];
    char          *data;
    unsigned long  len;
};

struct note *notes[MAXN];

static long readnum(void)
{
    char buf[0x20];
    memset(buf, 0, sizeof(buf));
    if (read(0, buf, sizeof(buf) - 1) <= 0)
        _exit(0);
    return atoi(buf);
}

static long readidx(void)
{
    printf("idx: ");
    return readnum();
}

static void menu(void)
{
    puts("\n--- jenotes - 100\% Secure Notes ---");
    puts("1. Add");
    puts("2. Edit");
    puts("3. Show");
    puts("4. List");
    puts("5. Delete");
    puts("6. Exit");
    printf("> ");
}

static void add(void)
{
    long i = readidx();
    if (i < 0 || i >= MAXN) { puts("bad idx"); return; }
    if (notes[i]) { puts("in use"); return; }

    char *buf = malloc(NOTELEN);
    if (!buf) { puts("alloc failed"); return; }

    struct note *n = malloc(sizeof(struct note));
    if (!n) { puts("alloc failed"); return; }

    memset(n, 0, sizeof(*n));
    n->data = buf;
    n->len  = NOTELEN;
    notes[i] = n;

    printf("name: ");
    read(0, n->name, sizeof(n->name) - 1);

    printf("data: ");
    read(0, n->data, n->len);
}

static void edit(void)
{
    long i = readidx();
    if (i < 0 || i >= MAXN || !notes[i]) { puts("bad idx"); return; }

    printf("data: ");
    read(0, notes[i]->data, notes[i]->len + 12);
}

static void show(void)
{
    long i = readidx();
    if (i < 0 || i >= MAXN || !notes[i]) { puts("bad idx"); return; }

    printf("%s\n", notes[i]->data);
}

static void list(void)
{
    for (long i = 0; i < MAXN; i++)
        if (notes[i])
            printf("%2ld: %.56s\n", i, notes[i]->name);
}

static void del(void)
{
    long i = readidx();
    if (i < 0 || i >= MAXN || !notes[i]) { puts("bad idx"); return; }

    free(notes[i]->data);
    free(notes[i]);
    notes[i] = NULL;
}

int main(void)
{
    setbuf(stdin,  NULL);
    setbuf(stdout, NULL);
    setbuf(stderr, NULL);

    for (;;) {
        menu();
        switch (readnum()) {
        case 1: add();  break;
        case 2: edit(); break;
        case 3: show(); break;
        case 4: list(); break;
        case 5: del();  break;
        case 6: puts("bye"); return 0;
        default: puts("?"); break;
        }
    }
}
