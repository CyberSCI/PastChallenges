FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends socat \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/bash ctf

WORKDIR /home/ctf

COPY one_gadget flag.txt ./

RUN chmod 555 one_gadget \
    && chmod 444 flag.txt

USER ctf
EXPOSE 1339

CMD ["socat", "TCP-LISTEN:1339,reuseaddr,fork", "EXEC:./one_gadget,stderr"]
