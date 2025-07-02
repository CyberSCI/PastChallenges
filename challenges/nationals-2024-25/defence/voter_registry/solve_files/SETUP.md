# Voter Registry Setup

## Server Setup

To connect to the Ubuntu VM:

```sh
ssh-keygen -f ~/.ssh/known_hosts -R 10.0.2.91
ssh vpcadmin@10.0.2.91
```

On the Ubuntu VM, install Docker:

```sh
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
rm get-docker.sh
sudo groupadd docker
sudo usermod -aG docker $USER
```

On the Ubuntu VM, install the `zip` package:

```sh
sudo apt install zip
```

On your client in the `challenges/defence/voter_registry/release_files/` directory, copy the `voter_registry.zip` file to a VM:

```sh
scp voter_registry.zip vpcadmin@10.0.2.91:~/
```

On the Ubuntu VM, unzip the file:

```sh
unzip voter_registry.zip
```


On the Ubuntu VM, setup the container:

```sh
cd voter_registry
sudo docker compose up -d --build
```

On the Ubuntu VM, re-run this command until the status is "Up X seconds (healthy)":

```sh
sudo docker compose ps
```

To run a basic test of the deployment from your client, go to the webpage:

https://register.valverde.vote

## Attacker Setup

The attacker setup depends on how Siege is set up, but some notes are:

1. `voter_registry_attacker/data/proofs/pdf.zip` must be unzipped such that the directory `voter_registry_attacker/data/proofs/pdf/` exists.
2. `voter_registry_attacker/data/proofs/png.zip` must be unzipped such that the directory `voter_registry_attacker/data/proofs/png/` exists.
3. The attacker itself needs the `requests` and `beautifulsoup4` Python packages installed.