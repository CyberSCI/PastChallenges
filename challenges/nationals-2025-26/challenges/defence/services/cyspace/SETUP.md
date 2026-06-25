# CySpace — Deployment Setup

End-to-end deployment for the defence-day infra:

1. team VM (the vulnerable service)
2. bot VM (the  attacker)


## Team VM (vulnerable service)

```bash
ssh vpcadmin@10.0.2.92
```

### 1. Install Docker

```bash
curl -fsSL https://get.docker.com -o install-docker.sh

sh install-docker.sh --dry-run

sh install-docker.sh

rm install-docker.sh
```

### 2. Drop the release tarball

The release bundle is **`release_files/`** of this challenge directory.
Build a tarball that contains exactly that subtree:

```bash
# On a build host
tar -czf cyspace-release.tar.gz -C cyspace release_files
```

Copy it to the team VM and extract:

```bash
scp cyspace-release.tar.gz vpcadmin@10.0.2.92:/home/vpcadmin
ssh vpcadmin@10.0.2.92
tar -xzf cyspace-release.tar.gz
cd release_files
```

### 3. Bring up the stack

```bash
sudo docker compose up -d --build
sudo docker compose ps        
sudo docker compose logs -f 
```

Quick check:

```bash
curl -sS http://localhost/ | grep -i 'cyspace'
curl -sS http://localhost/login.php | head -3
```

### 5. Snapshot the team VM

Before snapshot:

```bash
cat /dev/null > ~/.bash_history && history -c && exit

# Confirm auto-start on boot
sudo reboot
```

Reboot once to confirm `web` and `db` come up cleanly without operator
intervention. **Then** snapshot.

## Bot VM (attacker)

### 1. System deps

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git
```

### 2. Python venv + bot deps

The venv lives in `server_files/` (alongside `requirements.txt`):

```bash
cd server_files
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cd ..
```

The `siege` framework lives at `challenges/defence/siege/` and is **not**
pip-installed — the bot picks it up via `PYTHONPATH`. Either export it in
your shell or prefix every invocation:

```bash
export PYTHONPATH="$(git rev-parse --show-toplevel)/challenges/defence/siege"
```

### 4. Test the attacker

From the root defence folder: 

```bash
PYTHONPATH=./siege python -m siege.test_attacker cyspace cyspace_attacker.py CyspaceAttacker 10.0.2.92:80 1,2,3,4,5,-1,-2,-3,-4,-5
```