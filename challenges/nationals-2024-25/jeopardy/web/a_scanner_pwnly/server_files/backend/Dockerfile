FROM python:3.13-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

ENV PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY uv.lock pyproject.toml ./

RUN uv sync --frozen

COPY . .

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000/tcp

ENTRYPOINT [ "/app/docker-entrypoint.sh" ]
