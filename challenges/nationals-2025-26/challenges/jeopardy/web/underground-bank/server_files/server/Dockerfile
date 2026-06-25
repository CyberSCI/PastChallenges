FROM python:3.14
WORKDIR /app
RUN pip install 'fastapi[standard]' pyjwt
COPY main.py .
CMD ["python", "main.py"]
