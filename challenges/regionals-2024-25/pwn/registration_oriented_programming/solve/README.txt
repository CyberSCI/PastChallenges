The challenge reads strings into indices specified by the user. The
challenge can also print strings at all indices, up to the latest index.
There is no limit on the index specified by the user.

The user can read existing memory on the stack by adding a string to a high
index, then printing the list. This will print strings from all indices up
to the specified index, including pointers on the stack.

The intended solution uses this vulnerability to leak the libc address.

The user can then write strings to the index that coincides with the saved
return address, as well as the memory after it.

The intended solution uses this out-of-bounds write to write a ROP chain
and spawn a shell.
