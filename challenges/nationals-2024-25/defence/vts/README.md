# Vote Tabulation Service

## Description

This challenge simulates vulnerable vote tabulation service, whxih receives vote records from voting machines from all over the country. It is written in Lua. Communications are done over TCP with TLS.

The service attempts to validate incoming vote records, but does not do a very good job of it.

## Vulnerabilities

There are 5 vulnerabilities inside:

* Voting machine IDs are checke with CRC32 algorithm, which is vulnerable to hash clashes
* Voter impersonation is allowed (voter IDs are not checked)
* Voters are allowed to vote more than once
* Negative vote counts are allowed due to sign confusion
* There is an SQLi on candidate name

## Fixing the service

In order to fix vulnerabilities one would need to:
* Decompile the service code (using either [luadec](https://github.com/viruscamp/luadec) or [Lua Decompiler](https://luadec.metaworm.site/))
* Analyze the code and rename functions and variable to give them easier to understand names
* Monitor incoming requests and spot requests that exploit vulnerabilities
* Fix problems as they are identified. Suggested fixes can be found in [vts_fixed.lua](./vts_fixed.lua) (diff it with [vts.lua](./vts.lua))

## Setup

### On the build machine

* To build the challenge run `make`:

```
make all
```

* Pack up the files for the container 

```
tar zcf vts.tar.gz Dockerfile docker-compose.yaml vts.luc vts.db key.pem cert.pem
```

* Copy the package to the host machine:

```
scp ./vts.tar.gz vts:~
```

### On the host machine

* Install Docker:

```
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-compose
```

* Remove `tcpdump`

```
sudo apt-get remove tcpdump -y
```

* Unpack the files

```
tar xzf vts.tar.gz
```

* Run the container

```
sudo docker compose up -d --build
```

* Reboot the machine to make sure container will still run

* Clear all history and image

### On the bot machine

* Copy the following files to the bot machine:

```
scp vts_attacker.py bad-machine-ids.csv voter-list.csv bad-voter-list.csv candidates.csv machine-id-clashes.csv machine-ids.csv bot:~
```