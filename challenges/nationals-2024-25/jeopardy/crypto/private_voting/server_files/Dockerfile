FROM python:3.12-slim

RUN apt-get update && apt-get install socat netcat-openbsd -y && rm -rf /var/lib/apt/lists/*

RUN pip install pycryptodome

WORKDIR /app
COPY *.py .

EXPOSE 1337

ENV PYTHONUNBUFFERED 1

ENTRYPOINT ["socat", "TCP-LISTEN:1337,fork,reuseaddr", "EXEC:'python private_voting.py'"]