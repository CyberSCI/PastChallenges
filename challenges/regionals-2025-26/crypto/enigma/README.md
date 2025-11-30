# enigma

**Author:** silk

**Category:** crypto

## Description

This challenge is a crib/known plaintext attack on Enigma, the primary cryptosystem used by the Germans during World War 2.

### Files

```
release_files/encrypt.py
release_files/output.txt
```

### Host

N/A

## Part 1 

**CTFd name:** enigma

### CTFd Description

If it could be done in the 1940s, it could be done now.

The final decryption should be rather obvious, but just in case, it should match one of these SHA1 checksums:

```
8dfe2eb0bdb5f5e64ed82965b5e178eb7befaf30
996fa6e43e8991421c38d766b8c1676e6a18bb95
4e8842c9c4797f5e9298b1a96ccd9e098dae042e
```

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>

One of the following:
CYBERSCI 2026 AN UNBREAKABLE CODE SHOULD KEEP THE CYBERSCI COMMUNICATIONS SAFE
CYBERSCIXTWOZEROTWOSIXXANXUNBREAKABLEXCODEXSHOULDXKEEPXTHEXCYBERSCIXCOMMUNICATIONSXSAFE
CYBER SCIXT WOZER OTWOS IXXAN XUNBR EAKAB LEXCO DEXSH OULDX KEEPX THEXC YBERS CIXCO MMUNI CATIO NSXSA FE

</details>


### Walkthrough

<details>
<summary>(expand to read)</summary><br>

The encryption algorithm used is Enigma; the same cryptosystem used by Nazi Germany during WW2 and broken through the collaborative efforts of Polish, French, and British codebreakers.

To break this ciphertext, you must:
1. Determine the "crib" (known plaintext portion of the message): CYBERSCIXTWOZEROTWOSIX
2. Use the crib and a simulated Bombe machine to determine the approximate key sheet (rotors, initial rotor values, and partial plugboard pairs) used to encrypt the message.
3. Through further manual or automated means, modify the rotor ring settings, rotor initial values, and determine the remaining plugboard pairs.
4. Once a good-enough keysheet has been recovered, the final message can be decrypted (and re-formatted for easier reading).

Any of the following decrypted messages are acceptable:
CYBER SCIXT WOZER OTWOS IXXAN XUNBR EAKAB LEXCO DEXSH OULDX KEEPX THEXC YBERS CIXCO MMUNI CATIO NSXSA FE
CYBERSCIXTWOZEROTWOSIXXANXUNBREAKABLEXCODEXSHOULDXKEEPXTHEXCYBERSCIXCOMMUNICATIONSXSAFE
CYBERSCI 2026 AN UNBREAKABLE CODE SHOULD KEEP THE CYBERSCI COMMUNICATIONS SAFE

</details>

## Setup instructions

Upload the `encrypt.py` and `output.txt` files from the `release_files/` directory to CTFd. There is no infrastructure required for this challenge.