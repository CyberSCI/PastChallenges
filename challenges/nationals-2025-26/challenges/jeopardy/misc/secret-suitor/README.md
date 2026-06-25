# Secret Suitor

**Author:** Majeed (majkiwi)

**Category:** Misc

## Description

An OSINT challenge that starts with reverse searching an image, to find the location of a fort. The second step is finding archives relating to an old computer virus, the ILOVEYOU virus, that was reported about by an american defense organization in said fort.

### Files

Flag 1:

[location.png](./release_files/location.png)

Flag 2:

[note.pf](./release_files/note.pdf)

## Part 1

**CTFd name:** Secret Suitor 1

### CTFd Description

Welcome to the Post-EMP archivists team (or PEMPA for short)! While the whole world is scrambling to repurpose functional electronics, we at PEMPA believe it is more important to recover technological history. We have assigned you on the project of codename "Secret Suitor".

We found an unmarked picture in our archives (*location.png*), and need your help digging for some information.
The only information we have is that the picture was found in a file labeled "Fort". What is this referring to?

**Your task**: Find the name of the closest fort to where this picture was taken, and report back to us! We need the **fort's name** and the **city**.

*NOTE: Flag format is `CyberSci{<[a-z]+>}`, with the answer in the inner string containing only lowercase letters.*
*Example: the famous "Fort CyberSci" in "Ottawa" would be `CyberSci{fortcybersciottawa}`.*

### Depends on

None

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{fortmcphersonatlanta}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Players are expected to use an image reverse search tool, like Google Lens. Doing so, you can either focus on the orange/white building in the background or on the plate with "ONE" written on it. Both these elements, using Google Lens, lead to `One Tyler Perry Studios Way`, the address of a movie studio.

After finding the exact location which is in Atlanta, Georgia (USA), we can find the closest fort which is **Fort Mcpherson**, and that is the answer. The city is Atlanta as said before.

</details>

## Part 2

**CTFd name:** Secret Suitor 2

### CTFd Description

Just as the millenium began, the organization that was staying in this fort seemed to have been affected by an ancient technological threat, as shown by this hastily scribbled note that we retrieved... 
Find out the note's redacted information, and your mission will be complete.

**Your task**: Find the name of the threat (between 2 and 9 letters), followed by the exact local time of alert (`HHMM`, in military time).

*NOTE: Flag format is `CyberSci{<[a-z0-9]+>}`, with the answer in the inner string containing only lowercase letters and numbers. No spaces between words and numbers.*

### Depends on

Secret Suitor 1

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{iloveyou1555}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

The document scanned as pdf contains a hand-drawn logo of FORSCOM, and a note talking about "the [REDACTED] threat official alert at [REDACTED]". An address to fort McPherson is written at the end.

Using the zip code and the [logo](solve_files/logo.png), you must locate the organization that was headquartered in fort McPherson at the beginning of the millenium (~2000). Searching the exact address shows us it is FORSCOM (a part of the USA's army), and the logo confirms this answer.

Using the information we have, we must finally search for documents mentioning FORSCOM, a technological threat, and an official alert around the year 2000. The most notable threat you should find is the ILOVEYOU virus which affected FORSCOM heavily in the year 2000. A public archive of this threat can be found at : https://apps.dtic.mil/sti/tr/pdf/ADA415104.pdf

Finally, the document shows the exact events which happened, and we see that the official alert is actually an Information Assurance Vulnerability Alert (IAVA), which the document shows to have been transmitted at 1555 (3:55pm) local time.

The answers are therefore **iloveyou** and **1555**.


</details>

## Setup instructions

None
