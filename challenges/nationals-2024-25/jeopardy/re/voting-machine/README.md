# Voting Machine

**Author:** [0xd13a](https://github.com/0xd13a)

**Category:** RE / Hardware

## Description

This is a hardware challenge simulating a simple voting machine. It is built on Arduino Uno. Players can come to the organizers table to interact with the machine and try out some of the functionality.

Users log into the voting machine using a QR code from their voter ID card. Then they can use the buttons to select a candidate and vote for them. There is also an admin mode where one can submit the accumulated votes to the central server, and simulate a batch of votes for a single candidate.

### Files

[voting-machine.bin](release_files/voting-machine.bin)

[voting-machine-diagram.png](release_files/voting-machine-diagram.png)

[instructions.pdf](release_files/instructions.pdf)

## Part 1 

**CTFd name:** Voting Machine 1

### CTFd Description

Val Verde hired a company to build voting machines for their General Election. After doing a security audit of them you realize that they have a number of weaknesses in their design that may endanger the integrity of the election process.

It turns out that one of the voters on the voter list stored in the machine is an administrator, and scanning their registration card lets one into the hidden admin menu. Can you find out the name of the administrator?

You can verify the correct person by creating a QR code for them and scanning it on the machine.

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>

Luna Vizcaino *(limit the number of tries to 5)*

</details>


### Walkthrough

<details>
<summary>(expand to read)</summary><br>

To analyze the binary file with Ghidra use the following instructions: [1](https://github.com/thomasbbrunner/arduino-reverse-engineering), [2](https://www.jonaslieb.de/blog/arduino-ghidra-intro/).

This flag can be found by inspecting the compiled representation of [this code section](voting-machine.ino?#L470-L476).

For the solve code look at the [solve script](solve_files/solve.py).

</details>

## Part 2 

**CTFd name:** Voting Machine 2

### CTFd Description

Val Verde hired a company to build voting machines for their General Election. After doing a security audit of them you realize that they have a number of weaknesses in their design that may endanger the integrity of the election process.

There is apparently a secret combination of button presses that you can enter after you log in as a regular user, and you will be dropped into the admin menu. What is it?

Enter the sequence as a string of letters, e.g. `ADDCBE`.

You can verify the correct sequence by interacting with the machine.

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>

CEDEACCEDA

</details>


### Walkthrough

<details>
<summary>(expand to read)</summary><br>

This flag can be found by inspecting the compiled representation of [this code section](voting-machine.ino?#L546-L565).

For the solve code look at the [solve script](solve_files/solve.py).

</details>

## Part 3 

**CTFd name:** Voting Machine 3

### CTFd Description

Val Verde hired a company to build voting machines for their General Election. After doing a security audit of them you realize that they have a number of weaknesses in their design that may endanger the integrity of the election process.

The accumulated votes can be submitted to the Central Electoral Commission from the admin menu. The votes are encrypted with an embedded key. Can you find it?

Enter the encryption key matching `[0-9a-f]+`.

You can verify that you have found the correct encryption key by decrypting the following vote:

`E1 5B 30 50 7B EA 3D B0 C5 DE 6B 97 2B 71 B2 2D`

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>

39f43ed9818d1c49fd55e8af8ea3711f

</details>


### Walkthrough

<details>
<summary>(expand to read)</summary><br>

This flag can be found by inspecting the compiled representation of [this code section](voting-machine.ino?#L642-L669).

For the solve code look at the [solve script](solve_files/solve.py).

</details>


## Setup instructions

To build the challenge:

* Install Arduino IDE
* Build the voting machine using the attached diagram. 
  - For the screen use any [standard 16x2 LCD](https://docs.arduino.cc/learn/electronics/lcd-displays/) 
  - For the QR code scanner use the component from [these instructions](https://how2electronics.com/barcode-qr-code-reader-using-arduino-qr-scanner-module/). The component itself can be acquired [here](https://www.aliexpress.com/item/1005001975270917.html).
* Connect the board to IDE, compile and load the [voting-machine.ino](voting-machine.ino) file.
* Collect file `voting-machine.ino.with_bootloader.bin` from the build folder.