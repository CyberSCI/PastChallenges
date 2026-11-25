//  gcc -static -D_FORTIFY_SOURCE=0 -Os -no-pie -fno-stack-protector -w one_gadget.c -o one_gadget
#include <stdio.h>
#include <unistd.h>

void chal ()
{
    char buf[128];
    read(0, buf, 0x100);
    read(0, buf, 0x100);
}

void main ()
{
    asm ("syscall");
    write(STDOUT_FILENO, "Free overflow!: \n", 18);
    chal ();
    return 0;
}