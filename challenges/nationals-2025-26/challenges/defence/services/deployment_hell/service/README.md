# Deployment Hell

Welcome to Deployment Hell! You're the newest maintainer of our legacy CI/CD system. We've tried to modernize it as best we could, but there are definitely still some kinks to work out.

## Starting the system

Run this command to get everything up and running:

```bash
docker compose up --build
```

If you don't want logs clogging up your terminal, start the containers as daemons:

```bash
docker compose up -d --build
```

## Updating Jenkins config

You will notice a very useful JCasC (Jenkins Configuration as Code) file in [jenkins.yaml](./jenkins/casc/jenkins.yaml). You can apply new configuration to the Jenkins server by uploading/reuploading this file to the Jenkins instance.

## Restarting the system

If you need to restart any of the containers:

```bash
docker compose restart [container-name]
```

Note: Omitting the container name restarts all containers. Handy in a pinch!

## Emergency procedures

Ideally this _doesn't_ happen, but sometimes you might need to completely shut the system down.

```bash
docker compose stop
docker compose up --build [-d]

# FOR TRUE EMERGENCIES
docker compose down
docker compose up --build [-d]
```

# About Our Users

Sofia and Michael, and the Admin are pretty resilient folk -- at least the real ones are. If you change their passwords, they'll work around it, but you might need some extra elbow grease.
