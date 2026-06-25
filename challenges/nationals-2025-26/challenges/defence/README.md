# Defence Challenges

## Challenges in this repo

| Challenge | Author | Hooks (E/M/H) | Status |
| :--- | :--- | :---: | :--- |
| [CySpace](./cyspace) — period MySpace clone, PHP 5.6 + MariaDB | trenth | 1/2/2 | code-complete; deployment + dry run pending |
| [Deployment Hell](./deployment_hell)  | ApprenticeofEnder | 2/3/0 | Done |
| [Peak Science](./peak_science)  | Linden-Brochu | 0/3/0 | Done |
| [Banking](./banking)  | 0xd13a | 1/3/1 | Done |

## Siege framework (submodule)

The `siege/` directory is a git submodule pointing at [0xd13a/siege](https://github.com/0xd13a/siege). It is **not** populated by a normal `git clone`.

### First-time clone

```sh
git clone --recurse-submodules <repo-url>
```

Or, if already cloned without the flag:

```sh
git submodule update --init --recursive
```

### Pulling updates

After `git pull`, refresh submodules to the commit pinned by this repo:

```sh
git submodule update --init --recursive
```

To make this automatic on every `git pull`:

```sh
git config --global submodule.recurse true
```

### Bumping siege to a newer upstream commit

```sh
cd challenges/defence/siege
git pull origin main
cd -
git add challenges/defence/siege
git commit -m "Bump siege submodule"
```

# Setup instructions

## Prepare your SSH config for ease of operation

Set up `~/.ssh/config` as follows:

```
Host score
    HostName 52.186.155.230

Host bot
    HostName 10.0.2.90

Host peak
    HostName 10.0.2.91

Host cyspace
    HostName 10.0.2.92

Host deploy
    HostName 10.0.2.93

Host banking
    HostName 10.0.2.94

Host score bot peak cyspace deploy banking
    User vpcadmin
    IdentityFile MY_PRIVATE_KEY_FILE
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
```

## On the scoreboard machine

* Set up the machine

```sh
sudo apt update
sudo apt install -y python3 python3-pip
pip3 install gunicorn flask pycryptodome apscheduler jsonschema --break-system-packages
sudo apt install -y nginx
```

* Set up nginx

```sh
sudo rm /var/www/html/*
sudo mkdir /var/www/html/static
sudo chmod -R a+rxw /var/www/html
```

* Copy files

```sh
scp -r static/* score:/var/www/html/static
```

* Open up files

```sh
sudo chmod a+r /var/www/html/static/*
sudo chmod -R a+rx /etc/letsencrypt
```

* Set up Nginx SSL/TLS certificates

Request certificates by following instructions at https://certbot.eff.org/instructions?ws=nginx&os=ubuntufocal

* Copy library files to the scoreboard

```sh
scp -r siege score:~
```

* Create folder for logs:

```sh
mkdir ~/logs
```

* Edit Crontab by running `sudo crontab -e` and add the following lines at the end:

```
@reboot sudo -u vpcadmin /bin/bash -c 'cd /home/vpcadmin; PYTHONPATH=. python3 -u siege/siege_server.py -b /home/vpcadmin --cert /etc/letsencrypt/live/defence.thegreatreset.ca/fullchain.pem --key /etc/letsencrypt/live/defence.thegreatreset.ca/privkey.pem >> /home/vpcadmin/logs/console.log 2>&1'
```

* Reboot the machine

```sh
sudo reboot
```

## On every bot machine

* Set up the machine

```sh
sudo apt update
sudo apt install -y python3 python3-pip
pip3 install flask pycryptodome pwntools jsonschema typing_extensions --break-system-packages
```

* Copy library files to the bot

```sh
scp -r siege bot:~
```

* Copy attacker scripts (see instructions in individual repositories)

* Create folder for logs:

```sh
mkdir ~/logs
```

* Edit Crontab by running `sudo crontab -e` and add the following lines at the end:

```
@reboot sudo -u vpcadmin /bin/bash -c 'cd /home/vpcadmin; PYTHONPATH=. python3 -u siege/siege_bot.py >> /home/vpcadmin/logs/console.log 2>&1'
```

* Reboot the machine

```sh
sudo reboot
```

* See scoreboard at `https://defence.thegreatreset.ca/`

* Before the competition restrict ports 65500, 80, 443 to only be accessible from VPN

* Testing can be performed by setting up a tunnel (the scoreboard will be accessible at `https://127.0.0.1:4444`):

```sh
ssh -N -L 4444:defence.thegreatreset.ca:443 bot
```

* At the beginning of the competition make ports 80 and 443 accessible to everyone
