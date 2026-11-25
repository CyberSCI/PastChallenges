# jenotes 
CC      ?= gcc
JEFLAGS  = -m32 -O1 -fPIC -DPIC -w -Ilib/compat -Ilib -include lib/compat/fbsd_compat.h
CHALFLAGS= -m32 -O0 -fstack-protector-all -no-pie -fno-pie -Wl,-z,relro,-z,lazy -Wall

all: jenotes

je82.o: lib/fbsd82_malloc.c lib/rb.h lib/compat/fbsd_compat.h
	$(CC) $(JEFLAGS) -c lib/fbsd82_malloc.c -o $@

compat.o: lib/compat/compat.c
	$(CC) -m32 -O1 -w -Ilib/compat -c lib/compat/compat.c -o $@

jenotes: chal.c je82.o compat.o
	$(CC) $(CHALFLAGS) chal.c je82.o compat.o -o $@ -lpthread

clean:
	rm -f jenotes je82.o compat.o tools/layout_check

.PHONY: all clean

check: tools/layout_check.c je82.o
	$(CC) $(JEFLAGS) tools/layout_check.c lib/compat/compat.c -o tools/layout_check -lpthread
	./tools/layout_check

.PHONY: check
