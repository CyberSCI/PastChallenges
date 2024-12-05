FROM ubuntu:24.04

RUN apt-get update && apt-get -y install xinetd

RUN useradd -M ctf

WORKDIR /ctf

COPY xinetd.conf ./
COPY flag.txt ./
COPY challenge.sh ./
COPY polling_station ./

CMD ["xinetd", "-d", "-dontfork", "-f", "xinetd.conf"]
