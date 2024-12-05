The challenge will execute code at the address specified by the user, using
the `call` instruction.

By jumping in the middle of a function, RBP does not get updated and in
certain circumstances, the attacker can overwrite the return address of
nexted functions. This can be used to ROP.

The intended solution jumps to the middle of a function with a `fgets`
call, then overwrites the return address from `fgets`. ROP is used to leak
the address of libc by calling `puts` on a GOT entry. Then ROP chain is
used to call `main`.

The same attack is then repeated to call `system("/bin/sh")`.
