FROM ubuntu:22.04
WORKDIR /
RUN apt update
RUN apt install -y socat
RUN apt install -y yabasic
COPY inventory.bas .
COPY regular_inventory.csv .
COPY restricted_inventory.csv .
EXPOSE 10001
CMD ["socat", "tcp-l:10001,reuseaddr,fork", "SYSTEM:\"yabasic inventory.bas ; sleep 3\",pty,stderr"]