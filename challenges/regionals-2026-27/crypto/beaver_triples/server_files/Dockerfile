FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends socat && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY release_files/server.py .
ENV FLAG="CyberSci{tr1pl3s_4r3_0n3_t1m3_p4ds_n0t_r3cycl4bl3_l0gs}"
USER nobody
EXPOSE 1337
CMD ["socat", "TCP-LISTEN:1337,reuseaddr,fork", "EXEC:python3 -u server.py,stderr"]
