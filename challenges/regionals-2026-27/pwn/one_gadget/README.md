# one gadget

**Author:** _tyler_

**Category:** pwn

## Description

A very simple pwn challenge using the rt_sigreturn syscall to create a ROP chain and achieve RCE.

### Files

release_files/one_gadget.tar.xz

### Host
```
10.0.2.91
```
## Part 1

_Copy this section as many times as there are separate flags/steps in your challenge. They will be separate challenges in CTFd._

**CTFd name:** one gadget

### CTFd Description

I heard you like one gadgets, so I gave you just one useful gadget. Good luck!
```
nc 10.0.2.91 1339
```
### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>

cybersci26{m4yb3_w3_d0nt_n33d_s0_m4ny_g4dg3ts}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

All of this relies on the rt_sigreturn syscall, this is absolutely necessary for the challenge to be solved.
The rt_sigreturn frame is used to forge registers

3 stage ROP chain, main details of which are:
1. Stack pivot so that the stack points at .bss because rt sigreturn doesn't fit in the current read
2. Create a shell using the execve/execlp syscall (players can also try a ROP chain where they read the flag to stdout)

</details>

## Setup instructions



docker build -t one_gadget_chal .

docker run -d --restart always -p 1339:1339 --name one_gadget one_gadget_chal
