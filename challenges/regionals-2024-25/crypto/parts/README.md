# parts

## CTFd

### Category

Crypto

### Description

```
We've intercepted this high profile message. Can you find anything of value?

Flag format: `cybersci{[A-Za-z0-9_-]+}`
```

### Connection Info

N/A

### Files

[challenges/crypto/parts/release_files/parts.zip](./release_files/parts.zip)

## Walkthrough

Flag to give to sponsors: `cybersci{no_need_to_worry}`

```
This challenge is a message that's been insecurely encrypted with RSA.

With the included encryption script, you can see the encryption is small pieces each encrypted with an RSA public key (piece-wise/character-by-character encryption). This is an insecure method of encryption, which can be bruteforced.

Each piece is 4-bytes long, which means some optimizations may have to be done to bruteforce the pieces in a reasonable time.

After bruteforcing each piece, they can be combined to produce the plaintext:

> Plaintext: Let the President know there's cybersci{no_need_to_worry}. The election is under control
```

## Further Explanation

RSA encryption is only secure such that the domain of the plaintext is large enough to counter brute-force attacks. With a small domain of inputs, each ciphertext can be encrypted and compared to a given ciphertext.

Piece-wise encryption using RSA is insecure because it allows an attacker to bruteforce many insecure pieces instead of one large secure piece.

In this challenge, the pieces are still quite large, but still bruteforceable in a feasible amount of time with some optimizations.

Each piece is 4-bytes, or 32-bits. This means the input domain has a size of 2^32. By focusing on only printable ASCII characters, this input domain reduces to 100^4 or approximately 2^27.

A program can encrypt all 2^27 possibilities and check if the encrypted ciphertext matches any of the message's ciphertexts. If so, it saves the corresponding plaintext for that position. After trying all possibilities, all plaintexts should be discovered and the total plaintext can be printed.

## Deployment Instructions

There are no deployment instructions. This challenge does not require a server.