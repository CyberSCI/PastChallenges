FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    gfortran \
    make \
    socat \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN make all
CMD ["socat", "TCP-LISTEN:1010,fork", "EXEC:./hxch"]