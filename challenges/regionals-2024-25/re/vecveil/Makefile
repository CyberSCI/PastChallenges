.PHONY: all build vecveil genhash prepare cleanup

SRCDIR=src
BINDIR=bin
OBJDIR=obj

build: prepare vecveil genhash cleanup

vecveil:
	nasm -f elf64 $(SRCDIR)/vecveil.nasm -o $(OBJDIR)/vecveil.o
	ld -o $(BINDIR)/vecveil -s $(OBJDIR)/vecveil.o

genhash:
	nasm -f elf64 -g -F dwarf $(SRCDIR)/genhash.nasm -o $(OBJDIR)/genhash.o
	ld -lc -I /lib64/ld-linux-x86-64.so.2 -o $(BINDIR)/genhash $(OBJDIR)/genhash.o

prepare:
	mkdir -p $(BINDIR) $(OBJDIR)

cleanup:
	rm -rf $(OBJDIR)
