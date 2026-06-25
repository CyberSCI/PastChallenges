# Printer
Custom format string challenge.

```c
printt("!d", a);
// prints a
printt("!$2d", a, b);
// prints b
printt("!$-2d", a, b);
// prints b
printt("!+4d", a);
// prints *(a + 4)
printt("!+8+4d", a);
// prints *(*(a + 4) + 8)
printt("!$2+8+4d", a, b);
// prints *(*(b + 4) + 8)
printt("!+4n", a);
// Calls malloc(num_chars_printed) and assigns it to *a
// And copies the current buffer into the allocated chunk
```

So, we see that the `+X` feature essentially allows arb read, giving all leaks
We also allow positional specifiers and a way to dump the current written buffer into a chunk for use.

The bug is this. You know where everything is located using `+X`. 
You can use `!n` to first write a pointer into memory, then calculate the offet from the stack to the heap
and give a huge positional specifier to run `!n` on the point you wrote to memory
This essentially gives you the primitive
```c
*addr = malloc(written_sz)
memcpy(*addr, written_so_far, written_sz);
```

This is kinda like a arbitrary pointer write. From here, you can overwrite the tcache chunk and have 
`malloc` return an arbitrary value. From there you've escalated this to an arb write. One thing
to keep note is if `written_so_far` is empty then nothing is written. This allows your write value
to not be a writable address.

We'll give either with a old glibc version so it has `malloc_hook` or the binary will have a 
function pointer which you can overwrite to get `win`.

I prefer the second since it's similar to "classic" printf challenges and makes it look easier


