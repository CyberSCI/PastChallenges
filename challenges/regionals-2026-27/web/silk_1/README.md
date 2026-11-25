# steering ships

**Author:** silk

**Category:** Web

## Description

The goal of this challenge is to hack ship remote control software in an effort to build a dam using AI-controlled cargo ships.

One vulnerability (OpenID configuration is always fetched from the auth token's iss claim) leads to multiple problems:

1. The attacker can specify an arbitrary iss claim: "http://10.1.2.3"
2. This arbitrary OpenID issuer can be used to sign arbitrary JWT tokens and bypass authentication requirements.
3. This iss claim can also be used for SSRF.

### Files

`release_files/steering_ships.zip`

### Host

https://ships.damoverflow.com

## Part 1

**CTFd name:** steering ships 1

### CTFd Description

AI took our water, dams, and now our ships. Perhaps: two ships with one vuln?

### Depends on

N/A (allow all parts to be seen at once)

### Flag

<details>
<summary>(expand to read)</summary><br>

cybersci{sign3d_4nd_d4ted}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

For the first part of this challenge, the competitor must:

1. Identify that the Steering Ships' API trusts any authority/issuer (iss claim) in the OAuth 2.0 token and uses that authority's signing keys.
2. Start their own OAuth 2.0 authority server that will be used to forge tokens.
3. Forge a token using their own OAuth 2.0 authority.
4. Use the forged token to access the Steering Ships API, get a list of ship names, and get the flag from a ship's name.

</details>

## Part 2

**CTFd name:** steering ships 1

### CTFd Description

AI took our water, dams, and now our ships. Perhaps: two ships with one vuln?

### Depends on

N/A (allow all parts to be seen at once)

### Flag

<details>
<summary>(expand to read)</summary><br>

cybersci{sh1p_s1de_r3quest_f0rgery}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

For the second part of this challenge, the competitor must:

1. Identify that the Steering Ships' API sends a HTTP GET request to any authority/issuer (iss claim) in the OAuth 2.0 token.
2. Identify that "ship simulator" will expose the second flag if ever it detects a ship's "remote control" feature has been enabled (the competitor's goal is to hack and enable remote control of the ship).
3. Identify that a PUT request to unreachable legacy API can be used to enable a ship's remote control feature.
4. Identify that a GET request to the legacy API with the parameter `_method=PUT` will actually be processed as a PUT request.
5. Use the SSRF vulnerability + PUT request workaround to enable remote control of a ship (`GET /api/ships/{ship_id}/remote-control?_method=PUT&enabled=true&...`).
6. Fetch the flag from a ship's name after the "ship simulator" detects remote control has been enabled.

</details>

## Setup instructions

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

On your client in the `challenges/web/silk_1/` directory, copy the `server_files` directory to a VM (while ignoring .gitignore files):

```sh
rsync -rvzP --filter=':- .gitignore' ./server_files vpcadmin@10.0.2.11:~/
```

On the Ubuntu VM, fill out the `.env` file:

```sh
nano ~/server_files/steering_ships/.env
```

Enter the text (replace flag values with above flags and password with secure, random generated password):

```ini
KC_BOOTSTRAP_ADMIN_USERNAME=admin
KC_BOOTSTRAP_ADMIN_PASSWORD=
FLAG_1=cybersci{...}
FLAG_2=cybersci{...}
```

On the Ubuntu VM, generate a self-signed certificate:

```sh
openssl req -x509 -nodes -days 825 -newkey rsa:2048 -keyout ~/server_files/steering_ships/reverse-proxy/dev.key -out ~/server_files/steering_ships/reverse-proxy/dev.crt -subj "/CN=ships.damoverflow.com" -addext "subjectAltName=DNS:auth.ships.damoverflow.com,DNS:ships.damoverflow.com,DNS:api.ships.damoverflow.com" -addext "basicConstraints=critical,CA:FALSE" -addext "keyUsage=critical,digitalSignature,keyEncipherment" -addext "extendedKeyUsage=serverAuth"
```

On the Ubuntu VM, setup the container:

```sh
cd ~/server_files/steering_ships/
cp ../realm.json ./auth_server/
sudo docker compose up -d --build
```

On the Ubuntu VM, wait ~60 seconds and run this command to check the status is "Up X seconds (healthy)". Even if healthy immediately, Keycloak needs some time to initialize:

```sh
sudo docker compose ps
```

On the Ubuntu VM, reboot:

```sh
sudo reboot
```

To run a basic test of the deployment from your client:

1. Navigate to https://ships.damoverflow.com
2. Sign in using the admin username/password you defined in the .env file.
3. Enter a email/name for the admin profile if prompted.

To run a solve test of the deployment from your client, run (substite `<your_ip>` for your device's IP that is accessible by the server via OpenVPN):

```sh
pip install cryptography requests
export HOST_URL=http://<your_ip>:8000
python ./solve_files/asd.py
```

After running the basic test, reset the application's state by running this on the VM:

```sh
cd ~/server_files/steering_ships/
sudo docker compose down -v
sudo docker compose up -d
 history -c
```

On your client, generate the .zip file to provide to competitors:

```sh
git archive -o steering_ships.zip HEAD:challenges/web/silk_1/server_files . ':(exclude)realm.json'
```