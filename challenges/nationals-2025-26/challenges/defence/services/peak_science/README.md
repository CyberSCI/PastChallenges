# Peak Science Service Challenge

## Description

This is a vulnerable HPC app / heat diffusion model in fortran 77.
The user passes these values :
- A number of point solution
- The initial heat value of the plate
- The X and Y Coordinate of the changed heat value
- The new heat value at (X,Y)
- The delta time
- The number of step
- The simulation K parameter
- An optional command to pass to the application

## Vulnerabilities

There are 3 vulnerabilities in this application :
- The floating point data are not entirely sanitized against NaN letting the user run arbitrary commands
- A line in the analyzer code is too long and thus cut, letting some use case happening that shouldn't and dropping a password to the user
- A variable in the analyzer is badly assigned, leading to a division by zero (converting the number to Inf) and letting the user run arbitrary commands

The RCE and the password leak are intentional and are not the vulnerabilities themselves.
It is bad to have that tho. Don't do that.

## Setup

### On the build machine

* Pack up the files for the container

```sh
tar zcf heat-exchange-service.tar.gz Dockerfile docker-compose.yml hxch.f nlzr.f trtm.f makefile pswd
```

* Copy the package to the host machine:

```sh
scp ./heat-exchange-service.tar.gz host:~
```

### On the host machine

* Install Docker:

```sh
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-compose
```

* Unpack the files

```sh
tar xzf heat-exchange-service.tar.gz
```

* Run the container

```sh
sudo docker compose up -d
```

* Reboot the machine to make sure container will still run
