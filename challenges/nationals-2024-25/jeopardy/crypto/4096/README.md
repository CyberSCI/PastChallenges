# 4096

**Author:** silk

**Category:** crypto

## Description

This challenge is an insecure multi-prime RSA algorithm with x64 64-bit primes for a 4096-bit modulus. The modulus is feasible to factor with non-niave approaches, and after determining the primes, the ciphertext can be decrypted.

### Files

```
release_files/encrypt.py
release_files/output.txt
```

### Host

N/A

## Part 1 

**CTFd name:** 4096

### CTFd Description

This cipher looks similar to the last, but it may be too large to be cracked.

Flag format: `cybersci{...}`

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>


cybersci{on_y0ur_c0mm4nd}

</details>


### Walkthrough

<details>
<summary>(expand to read)</summary><br>

The encryption algorithm used is an insecure variant of multi-prime RSA. This algorithm uses x64 64-bit primes.

Unlike 256, a naive approach is much less feasible. However, factoring composites with primes of size 64-bits is still a feasible option with algorithms such as ECM (elliptic-curve factorization method). Other algorithms exist and can work, but ECM works great for this use case (many factors of low size).

1. Use an implementation of ECM (such as gmp-ecm) to factorize n.
2. Once the primes are found, you can compute the RSA private key.
3. With the RSA private key, you can decrypt the message.

</details>


## Setup instructions

Upload the `encrypt.py` and `output.txt` files from the `release_files/` directory to CTFd. There is no infrastructure required for this challenge.

### New Flag Instructions

In the event that the flag is leaked, these are the instructions to regenerate a new flag with a new `output.txt` file.

In the `server_files/` directory, enter a new flag in the `FLAG` variable. The total length of the text cannot exceed 511 characters.

Run the `encrypt.py` Python script. You may be required to run `pip install pycryptodome` before-hand.

Record the output to `output.txt`. Distribute this new `output.txt` to players.