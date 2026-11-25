FROM python:3.12.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && groupadd --system --gid 10001 damwatch \
    && useradd --system --uid 10001 --gid 10001 --no-create-home damwatch

COPY . /app/server_files
USER 10001:10001
EXPOSE 8000

CMD ["uvicorn", "server_files.app:build_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
