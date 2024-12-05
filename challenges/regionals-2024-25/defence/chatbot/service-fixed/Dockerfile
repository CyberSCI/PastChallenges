FROM python:3.9.20-alpine3.19

RUN pip install flask langchain-ollama langgraph ksuid

WORKDIR /app
COPY *.py .
COPY ./templates ./templates

CMD ["python", "app.py"]