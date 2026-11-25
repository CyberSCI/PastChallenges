# _D.I.Y Dam_

**Author:** _Anish Das / @Shlink_

**Category:** _Crypto_

## Description

_Decrypting a Transposition Cipher using given instructions. This challenge was inspired by and granted permission to use the Beaver Code Cipher by Lena Meier._

### Files

_`release_files/Instruction Manual.png`_

### Host

_N/A_

## Part 1

**CTFd name:** _D.I.Y Dam_

### CTFd Description

_Ever wanted to try making your own dam? Well better start now or you're never going to build your own dam!_

Task - Build a dam to reveal the hidden message.

### Depends on

_None. Players can solve this challenge in any order._

### Flag

<details>
<summary>(expand to read)</summary><br>

TOBEAVERORNOTTOBEAVERTHATISTHEQUESTION

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

_There are different possible solutions to this challenge, you can either write by hand or write by code. Solve file will be provided._

If player solves by other means, have them explain their process. However, this is what the decryption process should look like:
<img width="1538" height="1027" alt="D I Y DAM Cipher breakdown" src="https://github.com/user-attachments/assets/4cb2ed96-d44e-436d-84ae-1fa67daea2ca" />

1. Split Ciphertext in two as instructions say.
2. Split CT blocks in the same manner till each block contains no more than 1 or 2 characters, maintaining a tree format in a left to right array fashion.
3. Interleave block pairs together with the left block pair marked as odd positions and right block pair marked as even positions, it's 1-indexed (meaning left goes 1,3,5 and right goes 2,4,6).
4. Keep interleaving block pairs together in the same fashion till you recover the hidden message.
</details>

## Setup instructions

_Download the file located in `release_files/Instruction Manual.png`._
