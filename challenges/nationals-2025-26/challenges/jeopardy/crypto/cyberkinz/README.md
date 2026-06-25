# CyberKinz

**Author:** raed (crypto component); petiole (pwn component - separate challenge)

**Category:** Crypto

## Description

Before the EMP, CyberKinz were already a dying fad - digital pets on keychains, discontinued in 2001. After the EMP, someone figured out they still run on salvaged Game Boy hardware, and suddenly they're the hottest thing on the black market. Each unit comes with a registration key on its tag; bring it to a CyberKinz.com BBS terminal and unlock your pet's online profile. You've intercepted three registration keys from the same factory batch, along with the factory's leaked key-generation script. Rumour has it the factory's RNG never recovered from the EMP. Find the login credentials and log in.

### Files

[key0.txt](./release_files/key0.txt) - factory test card (plaintext documented in manual)

[key1.txt](./release_files/key1.txt)

[key2.txt](./release_files/key2.txt)

[key3.txt](./release_files/key3.txt)

[cyberkinz_manual.txt](./release_files/cyberkinz_manual.txt)

[factory_keygen.py](./release_files/factory_keygen.py)

### Host

`nc <host> <port>`

## Part 1

**CTFd name:** CyberKinz

### CTFd Description

> Before the EMP, CyberKinz were already a dying fad, digital pets on keychains, discontinued in 2001. After the EMP, someone figured out they still run on salvaged Game Boy hardware, and suddenly they're the hottest thing on the black market. Each unit comes with a registration key. Crack open the intercepted keys, find the credentials, and log in to the CyberKinz.com BBS terminal at `nc <host> <port>`. Three registration keys from the same factory batch were intercepted, along with the factory's leaked key-generation script. Rumour has it the factory's RNG never recovered from the EMP.
>
> `nc <host> <port>`
>
> Files: [key0.txt](attachment), [key1.txt](attachment), [key2.txt](attachment), [key3.txt](attachment), [cyberkinz_manual.txt](attachment), [factory_keygen.py](attachment)

### Depends on

None

### Flag

<details>
<summary>(expand to read)</summary><br>

`cybersci{r3us3d_k3ys_ar3_n0_k3ys-360163}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

#### Background: RC4 and the many-time pad

RC4 is a stream cipher - it takes a key and produces a pseudorandom **keystream** `K`. Encryption is just XOR: `C = P ⊕ K`. There is no IV or nonce; the keystream is determined entirely by the key. This means the rule is absolute: **never use the same key twice.**

When two messages are encrypted under the same keystream the key cancels on XOR:

```
C1 ⊕ C2 = (P1 ⊕ K) ⊕ (P2 ⊕ K) = P1 ⊕ P2
```

You now have the XOR of both plaintexts with no knowledge of the key. If you know *any* bytes of one plaintext, you immediately recover the corresponding bytes of the other. With a fully known plaintext (like the factory test card) you recover the entire keystream in one step and decrypt everything - a **known-plaintext attack**. This is why RC4 has been banned from TLS since RFC 7465 (2015) and why WEP, which reused RC4 keystreams, was catastrophically broken.

---

#### 1. Identify the vulnerability

Open `factory_keygen.py`. The critical lines are:

```python
BATCH_KEY = bytes.fromhex("<REDACTED>")   # one key for the whole batch

def encrypt_card(record_bytes):
    cipher = ARC4.new(BATCH_KEY)          # same key every call
    return cipher.encrypt(record_bytes).hex()
```

The comment at the top confirms it: *"The factory's hardware RNG was damaged during the EMP… The same BATCH_KEY is generated for every card in a single manufacturing batch."*

RC4 produces a deterministic keystream `K` from its key. If the same key is used for multiple messages, every ciphertext is just `C_i = P_i ⊕ K`. This is the **many-time pad** - a catastrophic reuse of a stream cipher.

#### 2. Find the known-plaintext anchor

Open `cyberkinz_manual.txt`. Near the bottom is the **Factory Test Key** section:

```
FACTORY TEST KEY (key0.txt)
---------------------------
Every manufacturing batch includes a factory quality-control test card
with fixed, publicly-documented credentials. Its encrypted key is shipped
as key0.txt. The plaintext of the test card is always:

    CYBERKINZ_REGISTRATION_CARD_v1
    PET_NAME......: FACTORY_TEST
    USERNAME......: TESTUSER
    PASSWORD......: TESTPASS
    SERIAL........: 0000000000000000
    ISSUED........: 2025-01-01
    END_OF_RECORD
```

`key0.txt` is the encryption of a **completely known plaintext**. Since `C0 = P0 ⊕ K`, we can recover the full keystream directly:

```
K = C0 ⊕ P0
```

This is a known-plaintext attack - no crib-dragging, no guessing. The keystream is 204 bytes long and covers every byte of every card.

#### 3. Recover the keystream

Reconstruct the known plaintext exactly as `factory_keygen.py` builds it - fixed-width fields, space-padded, single `\n` line endings:

```python
LABEL_PET    = b"PET_NAME......: "
LABEL_USER   = b"USERNAME......: "
LABEL_PASS   = b"PASSWORD......: "
LABEL_SERIAL = b"SERIAL........: "
LABEL_ISSUED = b"ISSUED........: "

TEST_CARD = (
    b"CYBERKINZ_REGISTRATION_CARD_v1\n"
    + LABEL_PET    + b"FACTORY_TEST    " + b"\n"
    + LABEL_USER   + b"TESTUSER        " + b"\n"
    + LABEL_PASS   + b"TESTPASS        " + b"\n"
    + LABEL_SERIAL + b"0000000000000000" + b"\n"
    + LABEL_ISSUED + b"2025-01-01"       + b"\n"
    + b"END_OF_RECORD\n"
)   # 204 bytes total

c0 = bytes.fromhex(open("key0.txt").read().strip())
keystream = bytes(a ^ b for a, b in zip(c0, TEST_CARD))
```

The field values are space-padded to exactly 16 bytes - match this precisely or the XOR will be off.

#### 4. Decrypt all three cards

Apply the recovered keystream to each of the three intercepted ciphertexts:

```python
def xor_bytes(a, b):
    return bytes(x ^ y for x, y in zip(a, b))

c1 = bytes.fromhex(open("key1.txt").read().strip())
c2 = bytes.fromhex(open("key2.txt").read().strip())
c3 = bytes.fromhex(open("key3.txt").read().strip())

p1 = xor_bytes(c1, keystream)
p2 = xor_bytes(c2, keystream)
p3 = xor_bytes(c3, keystream)
```

Each decrypted plaintext is a full 204-byte registration card. Print them and read off the `USERNAME` and `PASSWORD` fields from each.

#### 5. Parse credentials and log in

```python
def parse_card(plaintext):
    fields = {}
    for line in plaintext.decode(errors="replace").splitlines():
        if ": " in line:
            label, value = line.split(": ", 1)
            fields[label.rstrip(".")] = value.strip()
    return fields

for i, pt in enumerate([p1, p2, p3], 1):
    f = parse_card(pt)
    print(f"Card {i}: USERNAME={f['USERNAME']!r}  PASSWORD={f['PASSWORD']!r}")
```

Try each username/password pair against the server:

```
nc <host> <port>
```

One of the three cards belongs to the flag-bearing account. Sending its credentials returns the flag.

#### 6. Why the other two cards don't work

Two of the three cards are decoys with valid-looking credentials that the server rejects. Only the card registered to `alpha_unit` unlocks the flag. The server gives an identical error for wrong username and wrong password - no oracle to tell the pairs apart, just try all three.

The full automated solve is in `solve_files/solve.py`.

</details>

## Setup instructions

### One-time VM prerequisite: install Docker

```bash
ssh vpcadmin@10.0.2.81
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin make
sudo usermod -aG docker vpcadmin
newgrp docker
```

Verify with `docker run hello-world` before proceeding.

### Deploy

1. Generate keys: `cd server_files && make keys` - creates a Python venv, installs dependencies, runs `generate_keys.py`, and writes `key0.txt`–`key3.txt` to `release_files/` and `secret.txt` to `server_files/`.
2. Confirm `release_files/factory_keygen.py` shows `BATCH_KEY = bytes.fromhex("<REDACTED>")` - the real key must never appear in release files.
3. Copy server files to the VM (run from repo root):
   ```
   scp server_files/server.py server_files/secret.txt server_files/Dockerfile server_files/docker-compose.yml server_files/Makefile vpcadmin@10.0.2.81:~/cyberkinz/
   ```
4. SSH to the VM and start the server:
   ```
   ssh vpcadmin@10.0.2.81
   cd ~/cyberkinz && make run
   ```
5. To stop the server: `make stop` (from `~/cyberkinz` on the VM).
6. Verify end-to-end: `cd solve_files && python3 solve.py 10.0.2.81 1337` - should recover all three plaintexts via the key0 known-plaintext attack and print the flag.

### After a VM Restart

The Docker container does not start automatically on reboot. SSH to the VM and restart it:

```
ssh vpcadmin@10.0.2.81
cd ~/cyberkinz && make run
```

To make the container start automatically on boot, enable the Docker restart policy (already set to `unless-stopped` in `docker-compose.yml`) by ensuring Docker itself starts on boot:

```
sudo systemctl enable docker
```

This only needs to be run once. After that, future VM reboots will bring the container up automatically without manual intervention.
