FROM ubuntu:22.04
RUN apt update
RUN apt install -y python3 python3-pip git
RUN pip3 install flask jsonschema urllib3 PyYAML pwntools
WORKDIR /
RUN git clone https://github.com/0xd13a/siege
COPY site ./site
COPY config ./config
COPY services/inventory/attacker ./services/inventory/attacker
EXPOSE 80
ENV PYTHONPATH=./siege
CMD ["python3", "./siege/siege/siege_light.py"]