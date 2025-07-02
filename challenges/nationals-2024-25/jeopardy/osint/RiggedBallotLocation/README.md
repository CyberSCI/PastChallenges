# *Rigged Ballot Location*

**Author:** Shadow

**Category:** OSINT/Stego

## Description

An image file has been embedded with the flag in a txt file. Competitors will need to do some basic OSINT to find the owner of the location (the password) to retrieve the flag.

### Files

Image file - BallotRiggers.jpg  

### CTFd Description

Intel shows that this location is where the rigged ballots is being kept, however we are unaware of who owns this compound. We need the name to remove the issue, remember we need proof that the name is correct.  

### Flag

<details>
<summary>(expand to read)</summary><br>


CybersciNats{R1gged_B4llot_Stor4ge_290948}

</details>


### Walkthrough

<details>
<summary>(expand to read)</summary><br>

The description mentions that a name is needed and that proof is needed which should indicate the name is not the flag.  
Using steghide/similar tools shows that the image file contains another file and that it requires a password.  
The password is Arius which can be found by doing a reverse image search on the picture where multiple sources display that it is "Arius' Compound" from the movie Commando.  
The file that is extracted from the image file is Flag.txt

</details>
