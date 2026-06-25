# Factory-Defaults

**Author:** ES
**Category:** RE

## Description

- An PBX Management Server with no client binary provided to the player
- You need to figure out the protocol by reversing the server binary
- Craft a valid message to get the flag

### Files

`release_files/server`

### Host

`nc 10.0.2.151 5038`

## Part 1

**CTFd name:** Factory Defaults

### CTFd Description

Look at all these people, talking on the phone. Investigate this phone system to find the flag. Flag format: `CYBERSCI{...}`

More information can be found here: http://10.0.2.151/

### Flag

<details>
<summary>(expand to read)</summary><br>

`CYBERSCI{1t5_alw4y5_adm1n_4dm1n_3281}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

- Players have to find the admin password
- List the channels
- Send a message to print the channel info of the channel "flag" which contains the flag
- See solve_files/solve.py for a solve script (which I used claude to create, so it may not be the best quality)

</details>

## Setup instructions

* Install Docker on the VM

* Bring up the container:

```sh
sudo docker compose up -d
```