FROM debian:stable-slim

RUN dpkg --add-architecture i386 && apt update && apt install -y gcc libc6-dev socat libc6:i386

WORKDIR /home/ctf
COPY door_access /home/ctf/door_access
COPY physical_key_access_logs.txt /home/ctf/physical_key_access_logs.txt

RUN chmod 755 /home/ctf/door_access && chmod 444 /home/ctf/physical_key_access_logs.txt

