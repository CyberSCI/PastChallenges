FROM python:2.7-alpine

WORKDIR /app 

COPY requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt

COPY main.py /app/main.py

CMD [ "python", "/app/main.py" ]
