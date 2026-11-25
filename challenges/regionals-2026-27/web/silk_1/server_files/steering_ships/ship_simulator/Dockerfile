FROM python:3.12-slim

WORKDIR /app
COPY ship_simulator.py .

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

CMD ["python", "ship_simulator.py"]