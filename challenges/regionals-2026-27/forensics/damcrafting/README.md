# _Damcrafting_

**Author:** _lorg_

**Category:** _Forensics_

## Description

A forensics challenge that contains a network capture of client/server communications of someone playing Minecraft. Challenge contains two flags: one very easy, and one more challenging.

### Files

release_files/capture.pcap

### Host


## Part 1

**CTFd name:** Damcrafting 1

### CTFd Description

Not wanting the agents to overhear their strategic discussions, the beavers moved communications to an "encrypted" channel. Ok, maybe not so encrypted... Can you find what the beavers sent via this super secret protocol? 

Note: There are 2 flags in this pcap. If your flag doesn't work, it's probably the flag for part 2, which is unlocked after you solve part 1.

### Depends on


### Flag

<details>
<summary>(expand to read)</summary><br>

cybersci{b3av3rs_1n_m1necraft_WHEN???}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

PART 1 WALKTHROUGH: pcap has server/client traffic from a Minecraft session. Flag 1 can be found in plaintext in the in-game chat. It can be found by finding the correct packet in Wireshark, or running strings on the pcap.

</details>

## Setup instructions


## Part 2


**CTFd name:** Damcrafting 2

### CTFd Description

Ok, so that one was easy. Surely the agents won't be able to read THIS though... 

(Use the same PCAP as Part 1)

### Depends on

Damcrafting 1

### Flag

<details>
<summary>(expand to read)</summary><br>

CYBERSCI{B3AVER_FEV3R}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

PART 2 WALKTHROUGH: This flag is more challenging. Flag is hidden in the block placements. Players have to recreate the in-game movements to uncover the flag.

This can be done by parsing the traffic with a script to extract block\_place events and print their coordinates. These coordinates can then be plotted (with a script or online tools such as Desmos, graphmakeronline) to reveal the flag.

There are also Wireshark plugins such as MC Dissector that can parse the Minecraft protocol and reveal block placement coordinates.

The Minecraft protocol version is 26.1. This protocol is well-documented online.


</details>

## Setup instructions

