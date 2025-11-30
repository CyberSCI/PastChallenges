FROM python:3.13-slim-bookworm

ENV PASV_ADDRESS=127.0.0.1
ENV PASV_MIN_PORT=21100
ENV PASV_MAX_PORT=21110
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates vsftpd ftp iproute2

COPY vsftpd.conf /etc/vsftpd/vsftpd.conf.template

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY uv.lock pyproject.toml ./

RUN uv sync --frozen

COPY . .

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 13370/tcp

ENTRYPOINT [ "/app/docker-entrypoint.sh" ]
