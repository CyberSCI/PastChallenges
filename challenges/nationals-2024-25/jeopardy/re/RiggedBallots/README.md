# Rigged Ballots

**Author:** Shadow

**Category:** RE

## Description

Voter ballots which have been encoded or modified in some way by a program will need to be reversed to get the flag.

## Part 1 

**CTFd name:** Rigged Ballots

### CTFd Description

We have added a layer of encoding to ensure that the ballots cannot be tampered with, however General Esperanza has warned that there may be some rebels who have figured out the encoding. Ensure there are no false entries by decoding the ballots.

### Files

Flag.txt - has the flag and some other modified data  
Source - The executable that modifies the content for the competitors to figure out how to reverse the content in Flag.txt

### Flag

<details>
<summary>(expand to read)</summary><br>

CybersciNats{B0w_to_Esper4nza_03982}

</details>


### Walkthrough

<details>
<summary>(expand to read)</summary><br>

There is a solve script available but the following are the basic steps for reversing the content:
1. Add base64 padding
2. Decode from base64
3. XOR each character in the decode content with "Hail our leader and savior Esperanza"

The competitors are given a compiled ELF file, however the original source code was written in Python. Competitors will either need to decipher the compiled version or decompile to get the original source code back. 

Websites for decompile process:
- https://pyinstxtractor-web.netlify.app/
- https://pylingual.io/

</details>

## Part 2

**CTFd name:** Rigged Ballots 2

### CTFd Description

The rebels managed to decode our last ballot encoding somehow so now we have improved it. This should prevent any pesky rebels from knowing the real results of the election. The plan under General Esperanza shall go ahead as planned!

### Files

Ballots.txt - has the flag and some other modified data  
Source - The executable that modifies the content for the competitors to figure out how to reverse the content in Ballots.txt

### Flag

<details>
<summary>(expand to read)</summary><br>

CybersciNats{Sh1fting_3ncoding_30583}

</details>


### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Two scripts are available to do the manual tasks that would be tedious and time consuming but there are a few additional steps that would need to be undertaken to fully solve the challenge. The following are the overall steps that would need to be taken:
1. Determine how the ballots were scrambled (the order of ballots in the Ballots.txt)
2. Reverse each ballot [::-1]
3. Find the shift (25) can be done by checking against the Flag format which has kept the same structure as the previous challenge
4. Apply the shift to the characters that were shifted

The competitors are given a compiled ELF file, however the original source code was written in Python. Competitors will either need to decipher the compiled version or decompile to get the original source code back. 

Websites for decompile process:
- https://pyinstxtractor-web.netlify.app/
- https://pylingual.io/

</details>
