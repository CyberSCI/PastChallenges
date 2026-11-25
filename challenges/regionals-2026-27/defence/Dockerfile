FROM ubuntu:22.04
RUN apt update
RUN apt install -y python3 python3-pip git
RUN pip3 install flask jsonschema urllib3 PyYAML pwntools faker
WORKDIR /
RUN git clone https://github.com/0xd13a/siege
COPY site ./site
COPY config ./config
COPY services/log-monitor/attacker ./services/log-monitor/attacker
COPY services/greatdam/attacker ./services/greatdam/attacker
RUN pip3 install -r services/greatdam/attacker/requirements.txt 
RUN cd services/greatdam/attacker && tar -xzf log_requests.tar.gz
EXPOSE 80
ENV PYTHONPATH=./siege
CMD ["python3", "./siege/siege/siege_light.py"]
