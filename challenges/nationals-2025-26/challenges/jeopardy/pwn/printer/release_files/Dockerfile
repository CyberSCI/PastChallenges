FROM pwn.red/jail
COPY --from=ubuntu:24.10@sha256:cdf755952ed117f6126ff4e65810bf93767d4c38f5c7185b50ec1f1078b464cc / /srv
COPY main /srv/app/run
RUN chmod +x /srv/app/run
COPY flag.txt /srv/app/flag.txt
ENV JAIL_MEM=20M JAIL_ENV_NUM=5 JAIL_TMP_SIZE=10M