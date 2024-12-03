# SETUP

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

On your client in the `challenges/crypto/candidate_registry`, copy the `server_files` directory to a VM:

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
nc 10.0.2.11 10001
```

To run a solve test of the deployment from your client, run:

```sh
python3 solve_files/solve.py
```