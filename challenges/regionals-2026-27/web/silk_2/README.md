# Dam Beavers

**Author:** silk

**Category:** Web

## Description

The goal of this challenge is to hack an AI agent forum and read private posts related to their anti-beaver dam plans.

Two vulnerabilities allow this to happen:

1. Spoofing a user agent to look like Claude or another AI agent to have user registration auto-approved.
2. The admin report function, an open redirect, and the Python requests library's nature of appending custom headers to requests in a redirect chain allow you to steal an admin token.

### Files

`server_files/agent_commons.zip`

### Host

http://10.0.2.12:8000

## Part 1

**CTFd name:** dam beavers 1

### CTFd Description

The dam shall hold. The water must not flow.

### Depends on

N/A (allow all parts to be seen at once)

### Flag

<details>
<summary>(expand to read)</summary><br>

cybersci{w3lc0me_fell0w_ag3nt}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

For the first part of this challenge, the competitor must:

1. Identify that the user registration requires admin approval before you can login.
2. Identify that registering with an AI agent-related "User Agent" (such as "Claude-User/1.0") results in an auto approved registration.
3. Register using an AI agent user agent.
4. View user-only posts and capture the first flag.

</details>

## Part 2

**CTFd name:** dam beavers 2

### CTFd Description

The dam shall hold. The water must not flow.

### Depends on

N/A (allow all parts to be seen at once)

### Flag

<details>
<summary>(expand to read)</summary><br>

cybersci{its_a_cl0sed_l00p_4_sure}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

For the second part of this challenge, the competitor must:

1. Identify that the admin bot sends web requests to reported URLs, but URLs must be relative to the current website.
2. Identify that the current website has an open redirect vulnerability on the `/out` endpoint.
3. Identify that the admin bot's API token will persist through redirects and be sent to the redirected-to website.
4. Use the above three conditions to capture the admin bot's API token on a competitor web server.
5. Use the admin bot token to view hidden posts and capture the second flag.

</details>

## Setup instructions

To connect to the Ubuntu VM:

```sh
ssh-keygen -f ~/.ssh/known_hosts -R 10.0.2.12
ssh vpcadmin@10.0.2.12
```

On the Ubuntu VM, install Docker:

```sh
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

On your client in the `challenges/web/silk_2/` directory, copy the `server_files` directory to a VM (while ignoring .gitignore files):

```sh
rsync -rvzP --filter=':- .gitignore' ./server_files vpcadmin@10.0.2.12:~/
```

On the Ubuntu VM, fill out the `.env` file:

```sh
nano ~/server_files/agent_commons/.env
```

Enter the text (replace flag values with above flags; password with secure, random generated password; and secrets with random 32-character alphanumeric strings):

```ini
POSTGRES_PASSWORD=
DJANGO_SECRET_KEY=
JWT_SIGNING_KEY=
DJANGO_DEBUG=false
ALLOWED_HOSTS=localhost,127.0.0.1,web,10.0.2.12
WEB_PORT=8000
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=
FLAG_1=cybersci{...}
FLAG_2=cybersci{...}
BOT_FLAGGED_PATTERNS=bad bot
```

On the Ubuntu VM, setup the container:

```sh
cd ~/server_files/agent_commons/
sudo docker compose up -d --build
```

On the Ubuntu VM, wait ~60 seconds and run this command to check the status is "Up X seconds (healthy)":

```sh
sudo docker compose ps
```

On the Ubuntu VM, reboot:

```sh
sudo reboot
```

To run a basic test of the deployment from your client:

1. Navigate to http://10.0.2.12:8000
2. Sign in using the admin username/password you defined in the .env file: `curl http://10.0.2.12:8000/login/ -X POST -H "Content-Type: application/json" -d '{"username":"","password":""}'`
3. Check for an `access_token` value in the response.

To run a solve test of the deployment from your client, run (substite `<your_ip>` for your device's IP that is accessible by the server via OpenVPN):

```sh
export HOST_URL=http://<your_ip>:8001
python ./solve_files/asd.py
```

After running the basic test, reset the application's state by running this on the VM:

```sh
cd ~/server_files/agent_commons/
sudo docker compose down -v
sudo docker compose up -d
 history -c
```

On your client, generate the .zip file to provide to competitors:

```sh
git archive -o agent_commons.zip HEAD:challenges/web/silk_2/server_files .
```