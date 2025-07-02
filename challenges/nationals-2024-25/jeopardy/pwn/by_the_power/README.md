# By The Power of the key, open!

A PWN challenge with the overall goal of extracting a private key stored within a compiled binary.

## Release to contestants

The only file that should be released to the students is badge_firmware.

## Hosted keyserver

In order to validate the challenge a keyserver has been created in the `server` folder. This server will be hosted for each.

### Setup Keyserver

1. **Install Docker and Docker Compose on Ubuntu**

    ```sh
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
    sudo docker run hello-world
    ```

2. **Copy the `server` folder to your Ubuntu machine**

    First, create a tar archive of the `server` folder on your local machine:

    ```sh
    tar czvf server.tar.gz server
    ```

    Then, copy the archive to your Ubuntu machine (replace `vpcadmin` and `10.0.2.61` with your username and IP address):

    ```sh
    scp server.tar.gz vpcadmin@10.0.2.61:~/
    ```

    On your Ubuntu machine, extract the archive:

    ```sh
    tar xzvf server.tar.gz
    ```

3. **Start the keyserver using Docker Compose**

    ```sh
    cd ~/server
    docker-compose up --build -d
    ```

    The keyserver should now be running and accessible as configured.