# Spyware Challenges

This challenge consists of a malicious C2 server (disguised as a Cat Photo Exchange site), and an implant somwehere in the Linux machine. Malicious traffic is encrypted and attached to images exchanged between the 2 points.

![Screenshot](screenshot.png)

## Build

<details>
<summary>(expand to read)</summary>

The challenge consist of 2 parts - the malicious app and the command and control server. 

### To build the command and control server:

*On the build machine*

* Pack up the files for the container 

```
tar zcf c2-server.tar.gz Dockerfile docker-compose.yaml images/* c2-server/*
```

* Copy the package to the host machine:

```
scp ./c2-server.tar.gz 10.0.2.50:~
```

*On the server machine 10.0.2.50*

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

* Unpack the files

```
tar xzf c2-server.tar.gz
```

* Run the container

```
sudo docker compose up -d
```

* Reboot the machine to make sure container will still run


### To build the app:

* Copy `logmon.service` and `cat` to `10.0.2.52`

* Run `sudo mv logmon.service /etc/systemd/system`

* Run `sudo mv cat /etc/systemd/system`

* Run `sudo chmod a+x /etc/systemd/system/cat`

* Run `sudo chown root:root /etc/systemd/system/logmon.service /etc/systemd/system/cat`

* Run `sudo touch --reference=/etc/systemd/system/syslog.service /etc/systemd/system/logmon.service /etc/systemd/system/cat`

* Run `sudo systemctl daemon-reload`

* Run `sudo systemctl start logmon.service`

* Run `sudo systemctl enable logmon.service`

* Reboot the machine and check if the service is still running

* Clear history to hide the new files

</details>


## Spyware 1

### Description

> We have received intelligence that someone has planted a malicious application on the Electoral Commission's server (`10.0.2.52`). 
> Please help us identify it and figure out what it does. 
>
> Please analyze the machine, find this malicious application, and report its full path.


### Answer

<details>
<summary>(expand to read)</summary>

> **Flag:** `/etc/systemd/system/cat`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary>

One needs to look through running applications and find the app that is out of the ordinary. 

One could list all the running apps and check them to see if all of them are original apps that come with the OS.

It will help to see if an app is communication on the network.

It turns out that the app `/etc/systemd/system/cat` is not the original `cat` application, but rather the malicious implant we are looking for.

</details>

## Spyware 2

### Description

> We have received intelligence that someone has planted a malicious application on the Electoral Commission's server (`10.0.2.52`). 
> Please help us identify it and figure out what it does. 
>
> Communications between the app and the command and control server are encrypted. Can you figure out the phrase the encryption key is derived from?

### Answer

<details>
<summary>(expand to read)</summary>

> **Flag:** `¡Patria o Muerte!`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary>

The app communicates with what looks like a Cat Photo Exchange service at https://10.0.2.50:51829/. In reality, command and control traffic is attached to the images that are exchanged between the app and the server.

The encryption key is stored encoded in the application source. It is decoded before being used. One could re-trace the decoding steps to figure it out, or bypass anti-debug measures and debug the app to see the encryption key right before it is being used.

The key phrase is `¡Patria o Muerte!`.
</details>

## Spyware 3

### Description

> We have received intelligence that someone has planted a malicious application on the Electoral Commission's server (`10.0.2.52`). 
> Please help us identify it and figure out what it does. 
>
> We suspect that there is a special keyword the command and control server can send to shut down this spyware. Can you figure it out so that we could kill all instances of this malicious app across all government servers?

### Answer

<details>
<summary>(expand to read)</summary>

> **Flag:** `h45tA 1a V15tA, 8aBy!`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary>

In the application the keyword is determined by splitting it into 3-byte sequences, for each of which a stored SHA256 hash is verified. To figure out the keyword one can bruteforce the values for all keyword segments (which requires just a few minutes on an average machine).

The keyword is `h45tA 1a V15tA, 8aBy!`.

</details>

