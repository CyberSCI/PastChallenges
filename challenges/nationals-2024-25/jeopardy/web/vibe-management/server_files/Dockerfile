FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ADD ./vibe-management /app
WORKDIR /app

RUN uv sync --frozen

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0",  "--reload"]