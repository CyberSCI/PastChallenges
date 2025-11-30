FROM python:3.12-alpine

RUN apk add --no-cache chromium-chromedriver

COPY requirements.txt /customer_bot/requirements.txt
RUN pip install --no-cache-dir -r /customer_bot/requirements.txt

COPY customer_bot.py /customer_bot/customer_bot.py

CMD ["python", "/customer_bot/customer_bot.py"]