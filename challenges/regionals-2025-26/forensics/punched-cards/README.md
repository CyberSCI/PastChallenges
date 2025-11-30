# Punched cards

**Author:** Dmitriy Beryoza (0xd13a)

**Category:** Forensics

## Description

This challenge test players' skills at decoding puched cards and punched tapes.


## Part 1

**CTFd name:** Punched cards 1

### CTFd Description

We are trying to fire up several old IBM System/360 machines and we need to enter passwords to finish the startup sequences. The first one is encoded on this punched card but our IBM 1442 is broken. Can you please help decode it?

### Files

[punchedcard1.png](release_files/punchedcard1.png)

### Flag

<details>
<summary>(expand to read)</summary><br>

`CYBERSCI(AND_YOU_THOUGHT_FLOPPY_DISKS_WERE_WEIRD)`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Hand-decode the card using [this Wikipedia file](https://en.wikipedia.org/wiki/Punched_card#/media/File:Blue-punch-card-front-horiz.png)

</details>

## Part 2

**CTFd name:** Punched cards 2

### CTFd Description

This card encodes the password for the 2nd machine, but it's damaged and a part is missing. It will be more difficult to decode, but luckily the original engineers saved an MD2 hash of the password: `e809236d4b94e54174e666cf3b1f53ce`. Hope it helps...

### Files

[punchedcard2.png](release_files/punchedcard2.png)

### Flag

<details>
<summary>(expand to read)</summary><br>

`CYBERSCI(PUNCHC4RD_1S_7H3_FL4SH_ST0R@GE_OF_0LD!)`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Hand-decode the card using [this Wikipedia file](https://en.wikipedia.org/wiki/Punched_card#/media/File:Blue-punch-card-front-horiz.png) and then bruteforce the password using [this script](solve_files/brute-password.py).


</details>


## Part 3

**CTFd name:** Punched tape

### CTFd Description

We had the 3rd machine trucked in from the west coast and they forgot to send along the password for the startup sequence. All the regular comms are down, so they telegraphed it in. Our ITA2 telegraph machine is on the fritz. Can you decode the message?

### Files

[telegraph-message.png](release_files/telegraph-message.png)


### Flag

<details>
<summary>(expand to read)</summary><br>

`CYBERSCI(T3LEGR4PH-IS-Y0UR-GR4NDMA'5-INST4N7-M3SS4G1NG)`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Hand-decode the card using [this Wikipedia page](https://en.wikipedia.org/wiki/Baudot_code#ITA2)

</details>
