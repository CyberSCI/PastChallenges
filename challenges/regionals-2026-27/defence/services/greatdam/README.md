# Greatdam

**Author:** Linden Brochu

**Category:** Defense

## Description

The challenge is about securing a file system against path traversal attacks.

### Host

`ssh vpcadmin@10.0.2.21`
password : `vpcamdin`

## Part 1

**CTFd name:** The Great Dam - access logs

### CTFd Description

It is time to build a great dam - the greatest of them all.
And we'll make the AI pay for it.

The great dam's construction site has been set up.
An access system stores its logs into one of your systems.
Protect it.

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{M4gR3At10gs}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

The `monitoring-main` service serve as a filter to the `monitoring-fs` service.
In the filter, there is a line (`if !strings.HasPrefix(logRequest, "./")`) that filters basic requests,
but does not prevent a path traversal (for example `./..` is not blocked).
The recommended correction would be to minimize the `logRequest` and then look if it starts with `./`,
but any other correction that prevents a path traversal is acceptable.

</details>

## Setup instructions

### Optional - Create other logs

1. Run `datagen/gen.py`.
2. Run the services locally and run `datagen/select_and_gzip.py`.
3. Send the logs to the actual `dam-monitoring-fs` service.

### Setup

1. In the `dam-monitoring-fs` service, unpack the logs into `dam-monitoring-fs/logs`.
2. Run `docker compose up` to start the services.
3. For the attacker, unpack the log_requests into `attacker/log_requests`.
4. Install the required packages from the `attacker/requirements.txt`.
5. Setup siege.
6. Run the attacker.