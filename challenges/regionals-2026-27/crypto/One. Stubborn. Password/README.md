# _One. Stubborn. Password._

**Author:** _Anish Das / @Shlink_

**Category:** _Crypto_

## Description

_A Crypto challenge where players must perform a KPA (Known-Plaintext Attack) to recover the flag._

### Files

_`release_files/Passwords.txt`_

### Host

_N/A_

## Part 1

**CTFd name:** _One. Stubborn. Password._

### CTFd Description

_We just received an update, Chuck from Chewing Intelligence may have managed to get some valuable information that might aid in the fight against AI. However, Chuck forgot his password.. the beaver says it's so complicated to find that he made it too difficult to find it himself, we officially request that you help Chuck find his password._

Task - Find Chuck's password and capture the flag.
Note: Flag format will be CyberSci{...}

### Depends on

_None. Players can solve this challenge in any order._

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{P@SSWORD123}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

_There are many different ways to solve this challenge, however here is a quick walkthrough:_

- Use ROT13 and decode from Base64.
- There are many ways to go about this, use the given CyberChef Recipe to copy the output. Hit `CTRL + F` and find matching strings.
- Apply the decode steps from Step 1 and Voila!

CyberChef Recipe: https://gchq.github.io/CyberChef/#recipe=ROT13(true,true,false,13)To_Base64('A-Za-z0-9%2B/%3D')&input=Q3liZXJTY2l7

</details>

## Setup instructions

_Download the file located in `release_files/Passwords.txt`._
