# Beaver Tail

**Author:** 0xd13a

**Category:** RE

## Description

This challenge is an obfuscated stealer malware that one must reverse to find the flags.

## Part 1

**CTFd name:** Beaver Tail 1

### CTFd Description

We have found a previously unknown stealer variant of [BeaverTail malware](https://malpedia.caad.fkie.fraunhofer.de/details/js.beavertail) on our systems. We need your 'leet skills to analyze it and stop attacks on our community.

It is rumoured that the malware has a killswitch. Find it.

### Depends on

N/A

### Files

[beavertail.js](release_files/beavertail.js)

### Flag

<details>
<summary>(expand to read)</summary><br>

superintelligent

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Analysis of the code will show that there is a section that gets the current machine name and checks the BLAKE hash of its value against a constant. If the hash matches, malware quits. 

To find it get the [rockyou](https://weakpass.com/download/90/rockyou.txt.gz) password list and run it through the hash algorithm.

</details>

## Part 2

**CTFd name:** Beaver Tail 2

### CTFd Description

A remote operator that connects to the malware has to enter a password. Do you know what it is?

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{AI_will_crush_every_living_thing_in_its_way!}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

The password sent from malware operator is checked against a constant that looks like a flag embedded in the code, but it is a decoy. The submitted flag is run through a "twister" function first that converts it into the decoy. Reversing the twister algorithm (building a function that reverses it steps) and running the decoy constant through it gives the true flag. 

</details>

## Part 3

**CTFd name:** Beaver Tail 3

### CTFd Description

An important file was stolen from our document server. Luckily our firewall had packet capture turned on at the time...

### Depends on

Beaver Tail 2

### Files

[traffic.pcapng](release_files/traffic.pcapng)

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{The_defence_plan_is_no_longer_worth_a_dam}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Analysis of the algorithm shows that there is an AES encryption key that must be sent by the client during initial login. That key is used to encrypt subsequent communications. 

Use the key to decrypt the PCAP and recover an architectural drawing of beaver dam security systems that has a flag written on it.

</details>


## Setup instructions

To build the challenge we need to build 2 files:

* [beavertail.js](release_files/beavertail.js):
  * Open https://obfuscator.io/legacy-playground
  * Set desired obfuscation parameters
  * Use it to obfuscate [server.js](server_files/server.js)

* [traffic.pcapng](release_files/traffic.pcapng):
  * Run Wireshark in capture mode
  * Running a combination of [server.js](server_files/server.js) and [client.py](solve_files/client.py)
  * Log in to the server and get it to transfer [den-blueprint.png](server_files/den-blueprint.png)

[solve.py](solve_files/solve.py) is provided to prove the automated way to solve all 3 flags.