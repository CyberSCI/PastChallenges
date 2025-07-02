# 256

**Author:** silk

**Category:** crypto

## Description

This challenge is an insecure multi-prime RSA algorithm with x16 16-bit primes for a 256-bit modulus. The modulus is easy to factor, and after determining the primes, the ciphertext can be decrypted.

### Files

```
release_files/encrypt.py
release_files/output.txt
```

### Host

N/A

## Part 1 

**CTFd name:** 256

### CTFd Description

Through questionable means, this encryption algorithm was found on an adversary's computer along with one, last encrypted message.

Flag format: `cybersci{...}`

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>


cybersci{reest4bl1sh_on_4096}

</details>


### Walkthrough

<details>
<summary>(expand to read)</summary><br>

The encryption algorithm used is an insecure variant of multi-prime RSA. This algorithm uses x16 16-bit primes.

To solve this challenge, a naive approach works:
1. Each prime factor can be bruteforced as the range is only 0-65535.
2. Once the primes are found, you can compute the RSA private key.
3. With the RSA private key, you can decrypt the message.

</details>


## Setup instructions

Upload the `encrypt.py` and `output.txt` files from the `release_files/` directory to CTFd. There is no infrastructure required for this challenge.

### New Flag Instructions

In the event that the flag is leaked, these are the instructions to regenerate a new flag with a new `output.txt` file.

In the `server_files/` directory, enter a new flag in the `FLAG` variable. The total length of the text cannot exceed 31 characters.

Run the `encrypt.py` Python script. You may be required to run `pip install pycryptodome` before-hand.

Record the output to `output.txt`. Distribute this new `output.txt` to players.