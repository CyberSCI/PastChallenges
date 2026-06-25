FROM python:3.11-slim

WORKDIR /home/ctf
COPY server.py  /home/ctf/server.py
COPY secret.txt /home/ctf/secret.txt

RUN chmod 444 /home/ctf/secret.txt && chmod 755 /home/ctf/server.py && \
    useradd -m ctf

USER ctf

CMD ["python3", "server.py"]
