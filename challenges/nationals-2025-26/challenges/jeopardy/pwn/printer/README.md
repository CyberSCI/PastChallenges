# _CHALLENGE NAME_

**Author:** JoshL

**Category:** Pwn

## Description

Hand rolled format string pritner written in C. The bug should not be like a oob rw, (Use a format specifier that's not printf, like python f strings, or rust f strings).

### Files

- `printer`

### Host

- `nc -a <HOST> 5000`

## Part 1

**CTFd name:** Printer

### CTFd Description

GLIBC's printf was never that secure. So we wrote our own ontop of it to and made it more secure with more features!

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{from_the_stack_to_everything_to_heap_to_libc_to_binary...What_an_epic_tour}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Exploit details are in solve.py

</details>

## Setup instructions

1. Install docker
2. Run `docker compose up -d`
