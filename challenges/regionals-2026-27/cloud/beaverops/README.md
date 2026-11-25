# _BeaverOps_

**Author:** ApprenticeofEnder

**Category:** Cloud

## Description

A series of challenges surrounding CI/CD pipelines in ForgeJo.

### Files

`creds.json`

### Host

`http://beaverops.damoverflow.com:3000`

## Part 1

### CTFd name:

BeaverOps v0.1.0

### CTFd Description

The beavers are trying to build a CLI tool that plans dams. But like any good project, they need a CI/CD pipeline before they have shippable product.

See if you can't find a hole in it before someone worse does.

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{found_a_vein}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

This is a classic case of shell injection. However, a straight `echo` won't work, as ForgeJo doesn't print secrets to logs. You'll need to encode the message (double base64 plus a dummy string should do the trick).

Additionally, you may need to reconstruct some or all of the original command to avoid the CI/CD failing without printing out the flag.

For instance, input to the version parameter could look like:

```
1.0.0" '.version=$version' package.json > package.json.tmp && echo "$FLAG" | base64 -w 0 | base64 -w 0 && echo "DONE"
```

</details>

## Part 2

### CTFd name:

BeaverOps v0.2.0

### CTFd Description

Good find, keep it going. This one may need a little bit more digging.

### Depends on

BeaverOps v0.1.0

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{poisoning_the_well}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Obtaining flag 2 involves a cache poisoning attack. Using the `postinstall` feature of package.json, you'll need to write a script that injects malware into the PNPM cache. That malware needs to leak the flag from `process.env` either during the `pnpm install` phase, or the `pnpm build` phase. With this script, you'll make a PR against the main branch. You may need to run the workflow twice (once to poison the cache, then once to leak the flag.)

To poison the cache, we can override the `commander` package's `lib/command.js` file. PNPM uses hard links to save disk space, so we ideally want to edit the original file (just to avoid any filesystem annoyances).

We can get the original file with this command:

```bash
find ~/.local/share/pnpm/global/store/v11 -samefile $(readlink -f node_modules/commander/lib/command.js)
```

From there, modify the Command constructor to leak the FLAG environment variable. When the cli runs, the flag should be printed to stdout (albeit encoded, but you knew that from the first flag).
</details>

## Part 3

### CTFd name:

BeaverOps v0.3.0

### CTFd Description

You're on a roll. See if you can't hit them with something they'll never expect.

### Depends on

BeaverOps v0.2.0

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{who_let_the_packages_out}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

This one is a little more involved. You need to leverage Forgejo Authorized Integrations to create a release alongside a poisoned package.

1. Using the postinstall script, use the NPM token to publish a malicious version of the package that leaks the flag from process.env, similar to flag 2. This one doesn't need to modify the commander dependency.
2. Within that same postinstall script, [request an OIDC token from Forgejo](https://forgejo.org/docs/latest/user/api/authorized-integrations/#forgejo-actions-local) that can publish a release.
3. Since the `flag-3b.yml` workflow triggers on releases, it should download the malicious NPM package and leak the flag.

</details>

## Setup instructions

1. [VM] Install dependencies:

```bash
sudo apt install podman
curl --proto '=https' --tlsv1.2 -fsSL https://get.opentofu.org/install-opentofu.sh -o install-opentofu.sh
chmod +x install-opentofu.sh
./install-opentofu.sh --install-method deb
rm -f install-opentofu.sh
```

2. [Host] Copy all files in `server_files` to the VM:

```bash
scp -r server_files vpcadmin@beaverops.damoverflow.com:/home/vpcadmin/challenge
```

3. [VM] Copy the `.env.example` file in `challenge/config/forgejo` to a `.env` file in the same directory. Create a strong database password and update `FORGEJO__database__PASSWD` and `POSTGRES_PASSWORD`

4. [VM] Start the services:

```bash
cd challenge
sudo scripts/start.sh
```

NOTE: If the forgejo-runner doesn't start, it's not the end of the world right now. Just confirm the main forgejo service is up and running.

5. [Host] Navigate to `http://beaverops.damoverflow.com:3000` and confirm the following:
   a. The database settings were populated from the `.env` file
   b. The server domain is `beaverops.damoverflow.com`

6. [Host] Populate the "Administrator account settings" with values of your choosing and click "Install"

7. [VM] Initialize other ForgeJo assets via Terraform:

```bash
export FORGEJO_USERNAME="Chuck" # replace with your chosen value
export FORGEJO_PASSWORD="Password123!" # replace with your chosen value
export TF_VAR_forgejo_hostname="beaverops.damoverflow.com"
export TF_VAR_forgejo_username="Chuck" # change if replacing username
cd ~/challenge/infra
tofu init
tofu apply # this also initializes any ssh keys for git stuff
```

8. [VM] Upload the repository:

```bash
cd ~/challenge/repos/dam-builder
git config --global user.name Chuck
git config --global user.email chuck@damoverflow.com
git config --global init.defaultBranch main
git init
git add .
git commit -m "initial commit"
git remote add origin ssh://git@beaverops.damoverflow.com:2222/BeaverWorks/dam-builder.git
git push -u origin main
```

9. [Host] Create an Authorized Integration with the following parameters:

Name: Artifact Upload
Type: Forgejo Actions (Local)
Source Repository: BeaverWorks/dam-builder
Capabilities:

- package:write
- repository:write

10. [VM] Copy the Audience (aud claim) into the `flag-3a.yml` file as a comment, then push changes to the repo

11. [Host] Go to http://beaverops.damoverflow.com:3000/admin and navigate to Actions -> Runners

12. [Host] Click "Create new Runner" and fill in the details

13. [VM] Once you create the runner, copy the uuid and token into `~/challenge/config/forgejo/data/runner-config.yml` (leave the url alone)

14. [VM] Edit `~/challenge/containers/forgejo-runner.container` and comment out the DISABLE_RUNNER line.

15. [VM] Restart the services:

```bash
cd ~/challenge
sudo scripts/restart.sh
```
