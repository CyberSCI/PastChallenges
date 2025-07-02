# _ElectoMap_

**Author:** _Robert Babaev (ApprenticeofEnder/enderthenetrunner)_

**Category:** _Web/Cloud_

## Description

A visualization service to help the citizens of Val Verde see their votes in real time!

### Host

`http://electomap.valverde.vote:1337`

## Vulnerabilities

<details>
<summary>(expand to read)</summary><br>

1. The MQTT message broker used to transmit vote data across the system lacks any sort of access control. This means that votes can be intercepted and tied to the individuals making them.
2. No checks exist to verify whether a user has already voted.
3. Vote keys can be forged, since the JWT secret is left as a default that is relatively easy to crack or find via source code exposure.
4. Vote keys are not verified, so as long as the data maps to something in the database, users can submit arbitrary JWT payloads.
5. Duplicate national IDs can exist, leading to potential impersonation.
6. Fake votes can be submitted to the vote-counts topic, leading to disparity between the client and server
7. Users' national ID is exposed in the vote key payload.
8. A test account is hard-coded and active in the system, leading to potential for voting abuse if all other attempts fail.

</details>

## Patch Walkthrough

### Vulnerability 1

<details>
<summary>(expand to read)</summary><br>

There are a few potential fixes for this vulnerability. The first is to avoid using the `votes` topic entirely, and just have all of the processing occur within the `/api/votes` endpoint. However, given the intent to simulate a distributed, event-driven system, this isn't ideal.

The second approach involves adding access control lists and authorization checks to `mosquitto`. To do this, a few things will need to be modified.

**Note:** If you are having trouble with permissions, a good way to gain access to the configuration files is to spool up a Mosquitto container via Docker Compose:

```bash
docker compose run --rm mqtt /bin/sh
```

First, add the following lines to the `mosquitto.conf` file:

```
acl_file /mosquitto/config/electomap.acl
password_file /mosquitto/passwd_file
```

Next, add the `electomap.acl` file to the `mosquitto/config` folder:

```
topic read vote-counts

user electomap
topic vote-counts
topic votes
```

This allows read-only access to the anonymized `vote-counts` topic, while giving full access to the `electomap` user.

Next, modify the Dockerfile for Mosquitto to create a password file using the `mosquitto_passwd` command. Here is an example:

```Dockerfile
FROM docker.io/library/eclipse-mosquitto:2

ARG MQTT_USERNAME=electomap
ARG MQTT_PASSWORD=Td4TmbaEHpWVsu3YHs39nluuKEcwW0wwLY63nFQl5Ug

printf "${MQTT_PASSWORD}\n${MQTT_PASSWORD}\n" | mosquitto_passwd -c /mosquitto/passwd_file ${MQTT_USERNAME}
```

Finally, modify the MQTT client code in the SvelteKit app to use the new username and password supplied. It is good practice to use environment variables and secure passwords where possible.

In an ideal scenario, you would use build secrets where possible, but considering the images are not being uploaded, this is not as much of an issue.

</details>

### Vulnerability 2

<details>
<summary>(expand to read)</summary><br>

This vulnerability comes as a result of a lack of checks for duplicate votes. Here are some approaches and considerations:

1. Add a "hasVoted" boolean flag in the Users table and checking it while processing votes.
2. To avoid race conditions, use Drizzle's transaction feature and PostgreSQL's "SELECT FOR UPDATE".
3. When a user creates a vote key, check if they already have one - this may alleviate other potential vulnerabilities.

</details>

### Vulnerability 3

<details>
<summary>(expand to read)</summary><br>

Either set a secure default for the JWT secret (`node:crypto`'s `randomBytes` utility is helpful) or set the AUTH_SECRET environment variable.

</details>

### Vulnerability 4

<details>
<summary>(expand to read)</summary><br>

The app uses `jose.decodeJWT` rather than the correct `jose.jwtVerify` function. Remedy this and the vulnerability is solved.

</details>

### Vulnerability 5

<details>
<summary>(expand to read)</summary><br>

Add a uniqueness check for the national ID in the Users table itself. If you want to get fancy, add a try/catch for when duplicate IDs occur.

</details>

### Vulnerability 6

<details>
<summary>(expand to read)</summary><br>

Once again, the ideal solution for this is to add access control to Mosquitto. See #vulnerability-1

</details>

### Vulnerability 7

<details>
<summary>(expand to read)</summary><br>

Use the user ID rather than the national ID in the vote key. Change checks accordingly.

</details>

### Vulnerability 8

<details>
<summary>(expand to read)</summary><br>

Just delete the test account, it has no reason to be there in a live environment.

</details>

## Setup instructions

### Step 1 - Install Docker

```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo systemctl enable docker
sudo systemctl start docker
sudo groupadd docker
sudo usermod -aG docker $USER

# Log out and log back in

docker ps # test whether you can run docker commands as a non-root user
```

### Step 1.5 - Extract

If you are starting from the `base.tar.gz` file and nothing else, extract it first:

```bash
tar -xzf base.tar.gz
cd electomap
```

### Step 2 - Run

The service includes a script to build and run the entire system:

```bash
./scripts/up.sh
```

### Tearing Down

In the event of an emergency, the service includes a full teardown script:

```bash
./scripts/destroy.sh
```
