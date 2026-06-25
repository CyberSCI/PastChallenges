# _Assault and Battery_

**Author:** _ApprenticeofEnder_

**Category:** _Web_

## Description

A hybrid web/crypto challenge where players dig through logs to exploit a vulnerable custom onion hashing algorithm.

### Files

- `source.tar.xz`

### Host

`http://10.0.2.71:8000/`

## Part 1

**CTFd name:** _Assault and Battery 1_

### CTFd Description

As much as I'm happy to see a REST API again, not having a GUI to go with it is a little annoying.

Looks like the Reclaimers have a forum up, talking about batteries. I think they might be trying to power up some kind of resurrected LLM, but that's not the weirdest part about this whole operation.

May the Cleansing Light guide your way.

**Note**: _Offline_ brute-forcing, dictionary attacks, or other similar compute-intensive tasks may be necessary to complete this challenge.

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>

`CyberSci{S4l7_4nd_p3pp3r_f0r_74s7y_0ni0ns}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

It's possible to sign up for an account arbitrarily and access the logs from `/api/system/logs`. Narrowing down using the query parameters lets you find the logs from your own login. Given the username `hacker`, a request to `/api/systems/logs?username=hacker&size=1000` should give more than enough logs to find logs from the onion hasher in `authentication/hasher.py`. Writing a script to iterate through the (conveniently indexed) logs and crack the pepper character by character will reveal the flag.

</details>

## Part 2

**CTFd name:** _Assault and Battery 2_

### CTFd Description

Nice job on cracking the pepper. Now we need to figure out what all these gobbeldegook posts are on about.

Knowing these scumbags, they're probably like the clankers they used to use: All bark, very little bite.

**Note**: _Offline_ brute-forcing, dictionary attacks, or other similar compute-intensive tasks may be necessary to complete this challenge.

### Depends on

Assault and Battery 1

### Flag

<details>
<summary>(expand to read)</summary><br>

`CyberSci{V4ul7_cr4ck3d_7im3_70_sn00p}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

This is a matter of realizing that O-1 is an admin user and that all passwords for the existing users come from a known wordlist (`scripts/init_db.py`). If players extrapolate and use the same wordlist to try to crack O-1's password using the technique from the previous flag, they will be able to decrypt O-1's encrypted post and obtain the flag.

</details>

## Setup instructions

Steps 1 to 4 should be completed on both host and guest (i.e. challenge) machines.

1. Setup [Devenv](https://devenv.sh/getting-started/)
2. Install [Direnv](https://direnv.net/docs/installation.html#from-system-packages)
3. Add `eval "$(direnv hook bash)"` to the machine's `.bashrc` if it isn't there already
4. Start a new terminal session (usually you can exit and log back in)
5. On the host machine, `cd server_files && direnv allow` and wait for Direnv to finish building
6. `mkrelease && scp server.tar.xz vpcadmin@<HOST>:~`
7. On the guest machine, extract the challenge using `mkdir challenge && tar -xf server.tar.xz --directory ~/challenge`
8. `cd ~/challenge && direnv allow`
9. Wait for Devenv to finish building
10. `uv sync --frozen`
11. `init-db`
12. `sudo cp setup/challenge.service /etc/systemd/system/`
13. `sudo systemctl daemon-reload`
14. `sudo systemctl enable --now challenge.service`
15. Verify status: `sudo systemctl status challenge.service`
