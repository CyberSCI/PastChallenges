# private voting

**Author:** silk

**Category:** crypto

## Description

This challenge uses the Paillier cryptosystem to build a privacy-preserving voting counting machine and revealer.

### Files

```
release_files/private_voting.py
```

### Host

```
nc TODO_INSERT 1337
```

## Part 1 

**CTFd name:** private voting

### CTFd Description

To help combat voter intimidation, we designed a **secure** privacy-preserving voting system to help guard the privacy of the people of Val Verde.

Flag format: `cybersci{...}`

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>


cybersci{adds_t0_oNe_1s_n0t_en0ugh}

</details>


### Walkthrough

<details>
<summary>(expand to read)</summary><br>

This challenge uses Paillier encryption to build a flawed privacy-preserving voting system. In this system, the voting aggregator collecting encrypted votes, adds them together, and sends the encrypted total to the voting revealer. The voting revealer, using the private key, is able decrypt the total and reveal the winner. The voting aggregator does not have access to the private key, and therefore cannot decrypt individual voter's votes.

This system requires each voter to send N encrypted votes, one for each candidate (example: 0,0,1,0). Each vote is either a 0 or 1, with a 1 indicating the voter's decision. The voting aggregator is capable of summing together a voter's N encrypted votes and validating that the sum is equal to 1. This stops the voter from voting for multiple candidates (multiple 1s: 0,1,1,0), or voting multiple times for one candidate (value greater than 1: 0,0,2,0).

The flaw in this system is the voter can send an encrypted vote with a value greater than 1, and subtract that value from the other votes. This way, the sum of the values is still 1.
For example: 0,-100,101,0

To solve this challenge, you must write send an encrypted vote using the above mentioned exploit to rig the election in Gen. Ramon Esperanza's favor. Once Gen. Ramon Esperanza wins the election, the flag is printed.

</details>


## Setup instructions

To connect to the Ubuntu VM:

```sh
ssh-keygen -f ~/.ssh/known_hosts -R 10.0.2.11
ssh vpcadmin@10.0.2.11
```

On the Ubuntu VM, install Docker:

```sh
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

On your client in the `challenges/jeopardy/crypto/private_voting/` directory, copy the `server_files` directory to a VM:

```sh
scp -r server_files vpcadmin@10.0.2.11:~/
```

On the Ubuntu VM, setup the container:

```sh
cd server_files
sudo docker compose up -d --build
```

On the Ubuntu VM, re-run this command until the status is "Up X seconds (healthy)":

```sh
sudo docker compose ps
```

To run a basic test of the deployment from your client, run:

```sh
nc 10.0.2.11 1337
```

To run a solve test of the deployment from your client, run:

```sh
python3 solve_files/solve.py
```

### New Flag Instructions

In the event that the flag is leaked, these are the instructions to generate a new flag.

In the `server_files/secret.py` file, change the `FLAG` variable to contain the new flag.

Rebuild and restart the Docker container on the server (following the instructions above).