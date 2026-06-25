FROM ubuntu:22.04

WORKDIR /factory_defaults

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p ./site
COPY server .
COPY consumer .
COPY init-script.sh .
COPY dashboard.html ./site/index.html

RUN chmod +x ./init-script.sh

EXPOSE 5038
EXPOSE 80
ENTRYPOINT ["./init-script.sh"]