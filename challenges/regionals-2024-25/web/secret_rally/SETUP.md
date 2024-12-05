# SETUP

## Deployment Instructions

To connect to the Ubuntu VM:

```sh
ssh-keygen -f ~/.ssh/known_hosts -R 10.0.2.61
ssh vpcadmin@10.0.2.61
```

On the Ubuntu VM, install Docker:

```sh
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

On your client in the `challenges/crypto/candidate_registry`, copy the `server_files` directory to a VM:

```sh
scp -r server_files vpcadmin@10.0.2.61:~/
```

On the Ubuntu VM, setup the container:

```sh
cd server_files/secret_rally
sudo docker compose up -d --build
```

To run a basic test of the deployment from your client, navigate to: https://10.0.2.61

To run a solve test of the deployment from your client, run the following command. WARNING: This will cause the challenge to be in a solved state, and it must be reset before being provided to competitors.

```sh
python3 solve_files/solve.py
```

To reset the challenge, run these commands on the server:

```sh
cd ~/server_files/secret_rally
sudo docker compose down
sudo docker compose up -d --build
```