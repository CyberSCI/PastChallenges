# enigmail

**Author:** silk

**Category:** crypto

## Description

This challenge is a crib/known plaintext attack on Enigma with custom Base16 encoding and an unknown crib location.

### Files

```
release_files/enigmail.zip
```

### Host

N/A

## Part 1 

**CTFd name:** enigmail

### CTFd Description

Enigma > PGP

Flag format: `cybersci\{\w+\}`

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>

cybersci{just_use_pigeons_next_time}

</details>


### Walkthrough

<details>
<summary>(expand to read)</summary><br>

The encryption algorithm used is Enigma with a custom Base-16 encoding.

To break this ciphertext, you must:
1. Determine the "crib" (the included `logo.png` file's data).
2. Determine the location of the "crib" in the ciphertext (using a flaw in Enigma).
3. Use the crib and a simulated Bombe machine to determine the approximate key sheet (rotors, initial rotor values, and partial plugboard pairs) used to encrypt the message.
4. Through further manual or automated means, modify the rotor ring settings, rotor initial values, and determine the remaining plugboard pairs.
5. Backtrack to decrypt the parts of message before the crib.
6. Read the contents of the decrypted email and find the flag.

The decrypted email will look like this:

The person in the attached image has stolen multiple flags.
If you have any clues as to who this is, please advise.
cybersci{just_use_pigeons_next_time}

</details>

## Setup instructions

Upload the `enigmail.zip` file from the `release_files/` directory to CTFd. There is no infrastructure required for this challenge.