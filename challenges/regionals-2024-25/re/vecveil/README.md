# Vector Veil

An RE challenge featuring obfuscation through AVX2 and rudimentary anti-debugging techniques.

## Build

Ensure the following dependencies are installed:

- `make`
- `nasm`
- `ld`

Then, run `make` to build the binary. The binary will be output to `bin/vecveil`. Only `bin/vecveil` needs to be added to CTFd.

## Challenge

### Description

To streamline the election process, Val Verde has implemented a digital check-in system allowing voters to pre-register online and receive a unique digital code, replacing traditional ID checks at polling stations. The system verifies the code upon arrival to ensure only registered voters can proceed to vote. Although these check-in machines are closely guarded, the Central Electoral Commission (CEC) wants to ensure that the system remains secure even if someone gains access to one of the machines.

As a hired security consultant, your task is to evaluate the system's security. You are tasked with figuring out how to forge a registration code, demonstrating how an attacker might exploit the system to gain unauthorized access. Your findings will be crucial in securing Val Verde's election.

Your task is to analyze the binary further to uncover how the digital check-in system's authentication mechanism works. The system generates unique registration codes for each voter, and you must determine how these codes are created.

You are required to forge a valid registration code for General Mateo Alvarez. Successfully generating this code will simulate bypassing the check-in process and impersonating the General. The integrity of your nation rests in your hands!

Calculate the registration code for the name "Mateo Alvarez" and submit it as the flag.

### Answer

<details>
<summary>Click to reveal the answer</summary>

> **Flag**: `2882427855`

</details>

### Walkthrough

The walkthrough is available at [docs/WALKTHROUGH.md](docs/WALKTHROUGH.md).
