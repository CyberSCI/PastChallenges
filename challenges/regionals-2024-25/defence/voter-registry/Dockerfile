FROM ubuntu:22.04
RUN apt update
RUN apt install -y python3
RUN apt install -y python3-pip
RUN pip3 install flask pycryptodome PyJWT pyopenssl qrcode pyzbar pillow
RUN apt install -y zbar-tools
WORKDIR /
COPY voter_registry.py .
COPY add_template.html .
COPY admin_template.html .
COPY login_template.html .
COPY voter_template.html .
COPY voter-list.db .
COPY private_ed25519.pem .
COPY public_ed25519.pem .
COPY static ./static
CMD ["python3", "./voter_registry.py"]
