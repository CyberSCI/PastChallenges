# corporate complexity

**Author:** silk

**Category:** web

## Description

This challenge is a multi-container service that the player must build an attack chain to fully exploit.

### Files

```
release_files/corporate_complexity.zip
```

### Host

http://10.0.2.71:8080

## Part 1 

**CTFd name:** corporate complexity 1

### CTFd Description

So many jumps for such a simple system.

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>

cybersci{pl34se_upload_f0r_init4l_acc3ss}

</details>


### Walkthrough

<details>
<summary>(expand to read)</summary><br>

In the first part of this challenge, you must:

1. Upload a PHP file via the order submission service. This file can be a webshell, or other type of payload.
2. Predict the URL that can be used to access your `.php` file (MD5 hash of the file + `.php`).
3. Use the uploaded PHP file to run a command or code to read the `flag.txt` file.

</details>

## Part 2

**CTFd name:** corporate complexity 2

### CTFd Description

So many jumps for such a simple system.

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>

cybersci{p1v0t_and_c0nqu3r}

</details>


### Walkthrough

<details>
<summary>(expand to read)</summary><br>

In the second part of this challenge, you must:

1. Use the PHP webshell (or other payload) to send requests to the backend service.
2. In the request to the backend service, exploit the quantity parameter which is vulnerable to SQL injection.
3. Use the SQL injection vulnerability to extract the admin's password from the database, which is the flag.

</details>

## Part 3

**CTFd name:** corporate complexity 3

### CTFd Description

So many jumps for such a simple system.

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>

cybersci{s3nsit1ve_dat4_p1llag3d}

</details>


### Walkthrough

<details>
<summary>(expand to read)</summary><br>

In the third part of this challenge, you must:

1. Use the SQL injection vulnerability to write to the missing cron job script (`cleanup.old.sh`).
2. Wait for the script to be executed by the cron job.
3. Using a reverse shell or commands in the script itself - connect to the HR database using the known credentials (username/password is hr/hr).
4. Exfiltrate the flag from the HR database.

</details>

## Setup instructions

### Release files

Copy server_files to release_files and redact the following:

- `corporate_complexity/db_corpo/db_init.sql` (customer1 username/password, flag contents)
- `corporate_complexity/db_corpo/cleanup.sh` (corpo database password)
- `corporate_complexity/frontend/flag.txt` (flag contents)
- `corporate_complexity/docker-compose.yml` (corpo database password, all root database passwords, customer1 username/password)
- `corporate_complexity/db_hr/db_init.sql` (flag contents)

### Server instance

To connect to the Ubuntu VM:

```sh
ssh-keygen -f ~/.ssh/known_hosts -R 10.0.2.71
ssh vpcadmin@10.0.2.71
```

On the Ubuntu VM, install Docker:

```sh
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

On your client in the `challenges/jeopardy/crypto/private_voting/` directory, copy the `server_files` directory to a VM:

```sh
scp -r server_files vpcadmin@10.0.2.71:~/
```

On the Ubuntu VM, setup the container:

```sh
cd server_files/corporate_complexity/
sudo docker compose up -d --build
```

On the Ubuntu VM, re-run this command until the status is "Up X seconds (healthy)":

```sh
sudo docker compose ps
```

To run a basic test of the deployment from your client, run:

```sh
curl 10.0.2.71 8080
```

To run a solve test of the deployment from your client, run:

```sh
python3 solve_files/solve.py
```