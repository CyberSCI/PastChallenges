# Banking service

## Description

Banking service is written in Cobol and simulates an ATM machine.

## Vulnerabilities

There are 5 vulnerabilties defined:

- In **Deposit** function you can start a deposit, the balance will be updated, and then the transaction can be cancelled with balance still reflecting the deposit amount
- **Withdrawal** allows negative amout to be withdrawn, which increases the balance
- **Transfer** functionality allws transfer between accounts of more than available balance
- **Send** function has an error that cuts off part of the amount during the transaction
- **Pay** functionality allows payments to payees that are not registered

The version of the service with all vulnerabilities fixed can be found [here](./solution/banking.cbl)

## Setup

### On the build machine

* Pack up the files for the container 

```
tar zcf banking-service.tar.gz Dockerfile accounts.csv  banking.cbl  docker-compose.yaml  payees.csv  ssl.pem
```

* Copy the package to the host machine:

```
scp ./banking-service.tar.gz banking:~
```

### On the host machine

* Install Docker:

```
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl --no-pager status docker
sudo docker run hello-world
```

* Unpack the files

```
tar xzf banking-service.tar.gz
```

* Add `export HISTSIZE=0` to `~/.bashrc`

* Run the container

```
sudo docker compose up -d
```

* Reboot the machine to make sure container will still run

### On the bot machine

* Run the following to set up requirements:

```sh
pip install -r requirements.txt
```

* Disable updates for `pwntools`:

```sh
sudo sh -c 'echo "[update]\ninterval=never" > /etc/pwn.conf'
```