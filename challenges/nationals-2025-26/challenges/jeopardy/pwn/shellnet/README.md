# _CHALLENGE NAME_

**Author:** ApprenticeofEnder

**Category:** Pwn

## Description

A Telnet login wrapper that is not doing the greatest job of protecting itself.

### Files

- `shellnet`

### Host

- `telnet <HOST> 2333`

## Part 1

**CTFd name:** ShellNet

### CTFd Description

Damn, I thought this would be an easy win. First Telnet server I find and it's not even vulnerable.

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{dammit_the_validation_suck5}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Analyzing the binary reveals a gap in the shell stripping logic.

If you set the USER variable to `-f${IFS}root${IFS}` when running `telnet -a 2333`, you can log in as root and secure the flag.

</details>

## Setup instructions

Steps 1 to 4 should be completed on both host and guest (i.e. challenge) machines.

1. Setup [Devenv](https://devenv.sh/getting-started/)
2. Install [Direnv](https://direnv.net/docs/installation.html#from-system-packages)
3. Add `eval "$(direnv hook bash)"` to the machine's `.bashrc` if it isn't there already
4. Start a new terminal session (usually you can exit and log back in)
5. On the host machine, `cd server_files && direnv allow` and wait for Direnv to finish building
6. `mkrelease && scp server.tar.gz vpcadmin@<HOST>:~`
7. On the guest machine, extract the challenge using `mkdir challenge && tar -xf server.tar.gz --directory ~/challenge`
8. `cd ~/challenge && direnv allow`
9. Wait for Devenv to finish building
10. `sudo cp setup/challenge.service /etc/systemd/system/`
11. `sudo cp flag.txt /root/flag.txt`
12. `sudo systemctl daemon-reload`
13. `sudo systemctl enable --now challenge.service`
14. Verify status: `sudo systemctl status challenge.service`
