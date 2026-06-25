# LAST CONTACT
Author: t1v0

Category: Badge

## Description
A derelict field transceiver (the CyberSci 2026 badge). It powers up but the
network it belonged to went dark years ago. Across three steps the player
brings it back to life — **tune** the receiver, **key** in the recovered master
key, and **intercept** the message it starts broadcasting. It's part hardware,
part radio/CW lore, part crypto.

The badge is an nRF52840. It exposes a USB serial console (CDC-ACM) and a
Bluetooth LE radio. There are two firmwares: the **player** badge (handed out)
and 10 **mainframe** badges (worn by organizers) used in Part 2.

## Files
- **Players:** none — the physical badge *is* the challenge.

## Host
- **Part 1:** USB serial console. The badge enumerates as a CDC-ACM device named
  **"CyberSci Badge"** (Linux: `/dev/ttyACM0`; Windows/macOS: a COM/usbmodem
  port). It's USB CDC, so baud rate is irrelevant; open with any terminal
  (PuTTY / screen / minicom / VS Code Serial Monitor).
- **Parts 2 & 3:** Bluetooth LE, no pairing. Use a phone (**nRF Connect** is
  ideal) or a BLE sniffer (nRF Sniffer + Wireshark). The badge's own broadcast
  in Part 3 is a **non-connectable** beacon, so use a scanner that shows
  advertisements (nRF Connect shows it; Windows "Bluetooth LE Explorer" hides
  non-connectable beacons).

---

## Part 1

CTFd name: **Last Contact — Tune In**

### CTFd Description
You've recovered a dead field transceiver. It powers on, but the receiver is
detuned — nothing but static on the console, and a light on the panel pulsing in
the dark. Tune it to the right frequency to unlock it.

### Depends on
*(none — this is the first step)*

### Flag

<details>

`CyberSci{L4ST_C0NTACT_DE_SK}`

</details>



### Walkthrough
<details>

1. Power the badge. The 7-segment shows `2026`; the RGB strip blinks an amber
   pattern; the serial console scrolls "lost signal" static and swallows input.
2. The LED strip is blinking **Morse code**: it repeats the number **26**
   (`..--- -....`) with a long dark gap between repeats.
3. Convert the channel number to 8-bit binary: `26 = 0b0001 1010`.
4. Set the 8 DIP switches to that pattern. The firmware reads the bank as an
   8-bit value with the **top switch = most-significant bit**, and a switch in
   the **"1"/on** position = a `1` bit. So set the bank to read `0 0 0 1 1 0 1 0`.
5. On the correct value the console clears and prints the flag, a **CHANNEL CARD**
   (callsign / frequency / key group — needed for Part 3), and a `badge>` prompt;
   the LEDs settle to a slow dim-red "powered" breathe.

Note: if a player sets the switches *before* powering on, the badge unlocks
instantly and the banner scrolls past — `status` re-prints the flag and the
channel card at any time.
</details>


### Setup instructions

**Badges will be pre-flashed and locked** 


---

## Part 2

CTFd name: **Last Contact — Dead Transmission**

### CTFd Description
The receiver lives, but the network it belonged to is dark. Ten old mainframes
are still out there, each guarding a fragment of the master key — and each only
answers to someone who remembers how to talk to it. Find them, prove you belong,
collect the fragments, and **key** enough of them into your transceiver to
rebuild the signal.

### Depends on
**Last Contact — Tune In** *(the console shell only unlocks once the badge is tuned)*

### Flag

<details>

`CyberSci{D34D_TR4NSM1SS10N}`
</details>


### Walkthrough
<details>

The 10 mainframe badges each advertise an iconic system's name — a mix of
famous fictional computers and real legacy hardware — and serve a 32-byte
**Shamir secret-share** over GATT, gated behind that system's well-known
password / default credential (trivia). Any **7 of 10** shares reconstruct the
flag.

For each mainframe (using nRF Connect on a phone):
1. Scan; you'll see device names like `WOPR`, `ORACLE`, `VAX`, `SAP`, …
2. Connect. It has a custom service (UUID base `53525600-c1be-2026-4e4f-…`) with
   three characteristics, labelled via user-description: **SYSTEM** (`…0002`,
   read = the name), **LOGIN** (`…0003`, write the password), **KEYFRAG**
   (`…0004`, read — locked with an authentication error until you log in).
3. Recall the system's famous password / default credential and **write it to
   LOGIN** (as text; the badge normalizes case/spaces). E.g. `WOPR → joshua`,
   `ORACLE → tiger`.
4. **Read KEYFRAG** → 32 bytes. nRF Connect shows them as hex (64 chars).
5. On your badge console: `key <name> <64-hex>` — e.g. `key wopr <hex>`
   (multi-word names work: `key setec astronomy <hex>`). Each accepted share
   lights one more green segment on the LED strip.
6. After the **7th** valid share the badge auto-reconstructs the flag, prints it,
   the prompt turns green, the LEDs switch to a celebratory twinkle, and the
   radio comes **on the air** (this enables Part 3). No separate "decrypt" step.

The 10 nodes → AUTH password:

| # | Name | Write to LOGIN | Source | Expected fragment (KEYFRAG, 32-byte hex) |
|---|------|----------------|--------|------------------------------------------|
| 0 | WOPR | `joshua` | WarGames | `44445228c39acca164cee1e21259c93aabf05c3009ddc2e700c734b87b93334b` |
| 1 | THE GIBSON | `god` | Hackers (common password) | `c28d1b54fca0494b65bfd2aaa376c7b0c6c8f829df5d966e28401e7b0172c1a9` |
| 2 | SETEC ASTRONOMY | `too many secrets` | Sneakers (anagram of the name) | `1d0a2cce1e439d01582ac98f8af3ba0e17601874ca97ec1d43d357a7e3650549` |
| 3 | ORACLE | `tiger` | scott/tiger | `82236c830ec10055ac085ea5ea370e6311ed70e48f63338be68d705b297d0707` |
| 4 | VAX | `manager` | VMS SYSTEM/MANAGER | `02cce2da39c5c49311ec5c38e44cba375ed362dea583965bcd33f17bf579f1b6` |
| 5 | AS/400 | `qsecofr` | IBM midrange default | `4b762c09cddc062f771d4215d66b391263ee96a49e415b1f2c32cde6f83b877a` |
| 6 | IRIX | `4Dgifts` | SGI default account | `1323a587a9f2b96be8e6897ba7936d9062c66bbe99e5156a5c964ca2bdbb8660` |
| 7 | MIRAI | `xc3511` | IoT botnet root default | `49869f6211b7039976ce506f306668665cf80be2776cfd0a3a2a28173a8c9edf` |
| 8 | NETGEAR | `password` | admin/password | `a1ac101a0690c2cf393531c604d6c515f9028fa509d90c5eb12bd3c075c25877` |
| 9 | SAP | `06071992` | SAP* hardcoded default | `ecf9600398a8fe06941cfbfcdb7adc1257301483b5074e5a15e5f6caec87b791` |

The player badge stores only per-fragment CRCs and the flag CRC — never the
fragments or flag — so it must genuinely collect ≥7 real shares.
</details>


### Setup instructions

**Badges will be pre-flashed and locked** 


---

## Part 3

CTFd name: **Last Contact — Numbers Station**

### CTFd Description
With the master key rebuilt, your transceiver is back on the air — and it's
*transmitting*!  Decode the secret message!



### Depends on
**Last Contact — Dead Transmission** *(your badge only starts broadcasting once the key is rebuilt)*

### Flag
<details>

`CyberSci{N0W_BR04DC4ST1NG_0N_4LL_CH4NN3LS}`

(Same flag for every badge, even though each badge transmits a *different*
ciphertext — the per-badge key decodes them all to this.)
</details>


### Walkthrough

<details>

Once Part 2 is solved, the badge advertises a **numbers station** as a
non-connectable BLE beacon, modelled on the Cuban ¡Atención! station / Cuban
Five case. Read the **channel card** (`status` on the console, or the unlock
banner): it gives the **callsign** (e.g. `WMHG`, also the BLE device name so you
can pick out your own badge) and the **key group** (the one-time pad, 8 digits).

1. In a BLE scanner (nRF Connect, or a sniffer for reliability) watch the beacon
   named with your callsign. Its manufacturer data
   (`[company 0x1337][seq][total][5 digits]`) cycles ~1 s through 26 frames.
2. The 5 payload bytes per frame are **ASCII digits** (`0x30–0x39`). Capture a
   full cycle, order frames by the `seq` byte, and concatenate the digit groups
   → a 126-digit ciphertext string.
3. Decrypt with the key group, repeating it, by **mod-10 no-borrow subtraction**
   (the way the FBI decrypted ¡Atención!): `plain = (cipher − key) mod 10`.
4. Read the recovered digits in groups of **3** as decimal **CP437/ASCII** codes
   (`067 121 098 → C y b …`) → the flag.

Helper / verification (organizers): `firmware/tools/ch3_solve.py` mirrors the
firmware and self-tests. To decode a real capture:
```
python3 firmware/tools/ch3_solve.py "<all message digits in seq order>" "<key group>"
```

Because the callsign and pad derive from each badge's hardware UID, every badge
transmits a unique ciphertext that only its own key group decodes — a raw
capture can't be shared between players.
</details>


### Setup instructions

Full firmware, including both player and mainframe badges, flashing scripts and badge schematic are available in the zip file in this repository.

