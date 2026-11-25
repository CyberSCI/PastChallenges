# Defence Challenges

## Description

This is an attack service for all defence challenges. The front page gives buttons for executing pre-defined attacks against the services. If the vulnerability is fixed, a flag is revealed.

## Setup

### On the build machine

* Pack up the files for the container 

```
tar zcf attacker.tar.gz Dockerfile docker-compose.yaml site config services/log-monitor/attacker/* services/greatdam/attacker/*
```

* Copy the package to the host machine:

```
scp ./attacker.tar.gz 10.0.2.20:~
```

### On the host machine

* Install Docker:

```
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.dir/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
docker --version
docker compose version
sudo docker run hello-world
```

* Unpack the files

```
tar xzf attacker.tar.gz
```

* Run the container

```
sudo docker compose up -d
```

* Reboot the machine to make sure container will still run