FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN dpkg --add-architecture i386 \
    && apt-get update \
    && apt-get install -y --no-install-recommends socat libc6:i386 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/bash ctf

WORKDIR /home/ctf

COPY jenotes libc.so.6 ld-linux.so.2 flag.txt ./

RUN chmod 555 jenotes ld-linux.so.2 libc.so.6 \
    && chmod 444 flag.txt

USER ctf
EXPOSE 1341

CMD ["socat", "TCP-LISTEN:1341,reuseaddr,fork", "EXEC:./jenotes,stderr"]
