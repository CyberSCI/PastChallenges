# Avian Carrier Track

**Author:** Ch0ufleur

**Category:** RE (easy)

## Description

This challenge is about obtaining data from NFC chips embedded into real 3D-printed pigeon, and decoding that data with a provided program to obtain the flag. When data is corrupted, players should reverse the program or understand what has been corrupted.

### Files

avian_reader (ELF Binary)

### Host

N/A

## Part 1

**CTFd name:** Avian Carrier

### CTFd Description

When there's nothing else to depend on, pigeons become your best friends to carry information. I hear pigeon Rexxy is very dependable. **Suggestion : NFC Tools app -> Other -> Read memory.**

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{1nT3lh3X}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Players have to find a way to scan data from an NTAG215 Chip attached to a Pigeon. User Data starts at the fourth page of the hex dump. They know from testing using the binary that they have to recuperate 135 bytes of data in hex format.


Once they have stripped the hex dump from the chip of its chip headers and address data, they can select the first 135 bytes starting at the fourth page in memory, bundle it into a .hex file, and feed to the program to obtain the flag.

</details>

## Part 2

**CTFd name:** Corrupted Avian Carriers

### CTFd Description

When there's nothing else to depend on, pigeons become your best friends to carry information. Unfortunately, those other two pigeons are not as dependable as Rexxy, so we might not be able to read the data they were carrying... After all, many integrity mechanisms are in place for a reason!

### Depends on

`Avian Carrier`

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{so_m4ny_pigeons_63accd2_90}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Following the same extraction method as was used in the first flag, they have multiple different paths to figure out what is wrong. The easiest path is surely to look at the data in Cyberchef, notice that there's a weird byte in the middle of what should be the name Felix, correct the letter, then use the program to decode the first part of the flag. They could also attach gdb / figure out how the binary works and bypass the CRC check or patch it directly to that effect.


For the second part of the flag, nothing is obviously wrong with the payload. The easiest way to understand is mostly likely to attach gdb and find the check that bugs and clear it and/or patch it in the binary directly. They could also go down the rabbit hole and reverse the binary a bit more to understand how the decryption key is generated, and use it to decode the payload that is starting after the pigeon information bytes. It's possible that the decrypted packet could be found in memory with ltrace/ptrace, depending on the situation.

This is hence a easy-level RE challenge that plays on the Avian Carrier RFC idea, because the payload inside the NFC chip is actually an encrypted ICMP packet over IP :)

</details>

## Setup instructions

Hang pigeons physically in the challenge room.

### For testing purposes only:
NFC chips are NTAG215
You can use the dumps in solve_files/simulate_nfc_read
- exportAristotle.hex (flag 2)
- exportFelix.hex (flag 2)
- exportRexxy.hex (flag 1)

After manipulation of the data, a player should obtain the equivalent of the files dump1-3.hex, which are to be fed to avian_reader ELF Binary.



This information can also be useful:
- The .hex in **simulate_nfc_read/** for testing are in [Intel Hex format](https://en.wikipedia.org/wiki/Intel_HEX).
- Keep in mind players might have to deduce it.
