# candidate registry

## CTFd

### Category

Crypto

### Description

```
Only verified candidates can access this portal.. maybe we can be one?

Flag format: `cybersci{[A-Za-z0-9_-]+}`
```

### Connection Info

```
nc 10.0.2.11 10001
```

### Files

[challenges/crypto/candidate_registry/release_files/candidate_registry.zip](./release_files/candidate_registry.zip)

## Walkthrough

Flag to give to sponsors: `cybersci{pcbc_1s_n0t_cbc_dsh8sdj9}`

```
This challenge uses AES-PCBC (Propagating Cipher Clock Chain). A known vulnerability with this type of encryption is the ability to swap adjacent blocks in the ciphertext which only affects two plaintext blocks.

The purpose of the server is to receive encrypted payloads for registering candidates. A payload is only accepted if:
1. It's a valid JSON payload AFTER being decrypted with a secret key.
2. The payload contains the correct registration token.
3. The username is unique and has not been registered before.

The player is given an encrypted payload, but not given the encryption key or registration token.

Using the before-mentioned vulnerability, the player can swap two ciphertexts to create a payload the fulfills all the above conditions.

From the included scripts, you can infer the plaintext of encrypted message looks like this:
{"registration_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", "username": "davey_jones", "bio": "Once in power, I shall bring Valverdian's fleet to its former glory!"}

Swapping two blocks can result in the following decrypted output:
{"registration_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", "username": "davey_jo********************************hall bring Valverdian's fleet to its former glory!"}

Sending the maliciously crafted ciphertext will fulfill all the conditions, and the server will print this message:

> Here is your password: cybersci{pcbc_1s_n0t_cbc_dsh8sdj9}
```

## Deployment Instructions

Included in [SETUP.md](./SETUP.md).