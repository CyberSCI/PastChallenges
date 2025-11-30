# _Feed Me!_

**Author:** _David Gayowsky (twoaday)_

**Category:** _Crypto_

## Description

_This challenge is about reading carfully, and testing a player's ability to use data encodings, and general crypt knowledge (i.e. existance of older ciphers)._

### Files

_cybergotchi_user_manual.pdf_

_cybergotchi.gif_

### Host

_N/A_

## Part 1

**CTFd name:** _Feed Me!_

### CTFd Description

_Congratulations on the adoption of your new Cybergotchi! Remembr to pay close attention to your virtual pet, and read the user manual carfully before playing._

### Depends on

_N/A_

### Flag

<details>
<summary>(expand to read)</summary><br>

_CyberSci{my-virtual-pet}_

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

1. Retrieve the encoded flag from the Cybergotchi user manual: e922b7f439ed11d9fb764e1d74eba4b5133a4ba5e2d49a0052addb16da22e26d

2. Retrieve the plaintext key from the Cybergotchi gif file, noting down the button presses to give: BCACBACA

3. Convert the plaintext key to HEX: 4243414342414341

4. RC2 decode the encoded flag with the key 4243414342414341 with no IV and HEX input to retrieve the flag: CyberSci{my-virtual-pet}

Note that hints to properly decode are hidden throughout the user manual, e.g. button labels, RC2, no IV, HEX, when to begin the button press sequence, etc. The decoding can be easily done with CyberChef by plugging in details.

</details>

## Setup instructions

_Simply provide the files to the users, no installation required. Note these have been uploaded to CTFd within the challenge._
