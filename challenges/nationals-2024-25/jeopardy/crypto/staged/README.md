# staged

**Author:** silk

**Category:** crypto

## Description

This challenge uses many different ciphers/encodings applied iteratively to make a "ciphertext". Applying these ciphers/encodings in reverse reveals the plaintext.

### Files

```
release_files/cipher.txt
```

### Host

N/A

## Part 1 

**CTFd name:** staged

### CTFd Description

The chef sends his regards.

Flag format: `cybersci{...}`

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>


cybersci{4nd_th3n_the_n3xt_oNe}

</details>


### Walkthrough

<details>
<summary>(expand to read)</summary><br>

For this challenge, you are given a mess of a ciphertext without any other context. Following these steps grants you the flag:

1. Notice the initial ciphertext is a bunch of smiling and frowning emojis. This can be interpreted as a binary string (1s and 0s). Decode this ciphertext as binary.
2. Now we're given the hint "Caesar with a bit of spice from the chef". This implies a Caesar cipher, with something else. Applying a ROT13 shows the remaining ciphertext is only hexadecimal characters. We can then apply a Hex decode operation to receive the next ciphertext.
3. Now we're given the hint "*based* on *zip*". This, along with looking at the ciphertext, implies it is Base64 encoded. After Base64 decoding, we still have random binary data. We can either guess that this is Gzip compressed, or use CyberChef's "Detect File Type" feature to see its a Gzip file type. We can then apply the Gunzip operation to receive the next ciphertext.
4. Now we're given the hint "not not and and or". These are a bunch of boolean logic operations, and using these operations a logical XOR can be made. We can then apply the "XOR Brute Force" operation in Cyberchef to XOR the ciphertext with keys x00 to xFF.
5. We can finally see the flag decoded with "Key = 01".

</details>


## Setup instructions

Upload the `cipher.txt` file from the `release_files/` directory to CTFd. There is no infrastructure required for this challenge.