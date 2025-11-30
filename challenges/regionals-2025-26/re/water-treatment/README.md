# Water treatment

**Author:** Dmitriy Beryoza (0xd13a)

**Category:** RE

## Description

This challenge is a 16-bit DOS application that simulates managing a water treatment plant. 

### Files

[release_files/wt.exe](release_files/wt.exe)

## Part 1

**CTFd name:** Water treatment 1

### CTFd Description

We need to get our water treatment plant working again and we found an old IBM PC XT machine with specialized management software. We also need to locate the manual for it. For this, can you help us run it and figure out its official name?

### Flag

<details>
<summary>(expand to read)</summary><br>

`Neptune2000`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

This is a 16-bit DOS executable that will only run in DOS, Linux dosbox, or under a 32-bit version of Windows. Plyers need to figure out how to run it to get the official name written in ASCII art (`Neptune2000`).

</details>

## Part 2

**CTFd name:** Water treatment 2

### CTFd Description

We got the program running, but now it asks for the password. We are not sure what it is. You will have to analyze the executable and try a bunch of variants.

### Flag

<details>
<summary>(expand to read)</summary><br>

`waterworkz`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

This step requires reversing. The password is checked by verifying its MD2 hash (`9e46248d91fdcbecb3f4ba7caae38b0d`). You need to write a script to go through a list of common passwords (`rockyou.txt`). 

</details>

## Part 3

**CTFd name:** Water treatment 3

### CTFd Description

Adding chlorine to water is a dangerous operation, so it requires a special code to be entered. Can you figure out what it is?

### Flag

<details>
<summary>(expand to read)</summary><br>

`Aqu@Sh0cK!`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

This step also requires reversing. Security code is checked by verifying [scan codes](https://kbdlayout.info/kbdusx/scancodes) of the keys pressed.

</details>

## Setup instructions

**To build the challenge**

* Dowload and unpack [Open Watcom C compiler zip file](https://openwatcom.org/ftp/install/open-watcom-c-linux-1.9) into `server_files/ow/`
* Run `make` in `server_files/` to build `wt.exe`
