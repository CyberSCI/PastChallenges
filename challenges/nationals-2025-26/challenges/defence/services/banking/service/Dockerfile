FROM ubuntu:22.04

WORKDIR /banking

COPY banking.cbl .
COPY accounts.csv .
COPY payees.csv .
COPY ssl.pem .

RUN apt update \
    && apt install -y --no-install-recommends gnucobol socat ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN cobc -free -x banking.cbl -o banking

EXPOSE 10001
CMD ["socat", "-t", "0", "openssl-listen:10001,cert=ssl.pem,verify=0,reuseaddr,fork", "EXEC:\"./banking\",pty,stderr"]
