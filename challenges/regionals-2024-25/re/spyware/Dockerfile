FROM ubuntu:22.04
RUN apt update
RUN apt install -y python3
RUN apt install -y python3-pip
RUN pip3 install flask pycryptodome pyopenssl
WORKDIR /spyware
COPY c2-server ./c2-server
COPY images ./images
CMD ["/bin/sh", "-c", "cd ./c2-server; python3 ./c2-server.py >> c2-server.log 2>&1"]
