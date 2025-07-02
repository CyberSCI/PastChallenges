# Misprotected

Since the walkthrough for this challenge is too long. It has been put into a separate file at: [WALKTHROUGH.md](walkthrough/WALKTHROUGH.md).

## Files

The following file should be made available for download by the participants:

- `./ValVotaBallotManualEntry/ValVotaBallotManualEntry.zip`

## Part 1 (Misprotected 1)

### CTFd Description

```markdown
## Background

> You must be the new security engineer. You came in just in time.
>
> You see, during the last election, some of the voting machines in the Verdantia region broke down. They had to wait five extra days for the replacement voting machines to be installed, which delayed the conclusion of the election by five days. People started spreading conspiracy theories that the votes were being manipulated.
>
> To prevent that disaster from happening again, we asked the manufacturer to fix the defects in the voting machines. As a precaution, Ricardo's team also developed this manual ballot submission software as a backup so that if all the machines fail again, at least they can count the votes manually and submit the results through this software—which will be faster than waiting for replacement voting machines to be installed.
>
> The software is supposed to work only when authorization is given; otherwise, people could tamper with the voting results. I heard that they bought some fancy tools that will "guarantee" its safety, but I don't really buy their snake oil. Ricardo's team doesn't have any security professionals, and I have this funny feeling that they don't even know how to use the thing properly. I tried to get some budget from Chief Electoral Officer Gabriel to hire a new team of security professionals to redo it, but he thinks it's redundant.
>
> Your task is straightforward: I need you to crack that software open and submit an abnormal number of votes to prove that their security is nonsense, so I can take this to Gabriel and get him to approve that budget and hire more proper security professionals.

## Objective

This challenge consists of two parts. In the first part, your goal is to bypass the authorization mechanisms and gain unauthorized access to the software's functionalities. In the second part, you will need to submit an abnormal number of votes.

For this part of the challenge, once you crack the authorization mechanisms and get to the "homepage" of the software, the flag will be clearly visible on the UI.
```

### Flag

<details>
<summary>click to expand</summary>

`flag{b3tteR_L3arN_H0W_T0_u5E_THe_TOoLs_yOU_bOuGHt}`

</details>

## Part 2 (Misprotected 2)

### Depends On

- Misprotected 1

### CTFd Description

```markdown
Nice work breaking into the software!

For this part, your task is to submit more votes for a region than there are eligible voters in that region. For example the Verdantia region has 12,125,863 eligible voters. You need to make an submission where the sum of the votes of all candidates exceeds this number, like 999,999,999 votes for Esteban de Souza. Once you do that, the server should return the flag in its response.

How you achieve this is entirely up to you—just know that the server isn't designed to be vulnerable or exploitable. If you do end up breaking the server somehow, please let the organizers know so they can fix it.
```

### Flag

<details>
<summary>click to expand</summary>

`flag{g1mm3_g1mm3_g1mm3_an_ex7r4_v0t3_aft3r_m1dnight}`

</details>
