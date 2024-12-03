The main bug is that the length used by `strlcpy` can be 0xffffffffffffffff
when `read` returns with an error code. This can be used in a heap
overflow and to leak data from the heap.

Another useful bug is that the `poll` call will return an event for out-of-
band data, but the program does not attempt to read this data. This lets an
attacker hang the process, waiting for normal data. This is used to
reliably groom the heap, as data can be sent and queued to be read while
in this hung state.

The intended solution leaks the libc address from a chunk in an unsorted
bin and a heap address from a tcache chunk. Then, the overflow is used to
poison a tcache chunk, creating a fake chunk in the GOT. This is used to
overwrite the `fwrite` GOT entry with `system`. Data is then sent with the
string "/bin/sh" to call this function and spawn a shell.
