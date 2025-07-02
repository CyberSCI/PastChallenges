FROM ubuntu:22.04
RUN apt update
RUN apt install -y lua5.3
RUN apt install -y liblua5.3-dev
RUN apt install -y luarocks
RUN apt install -y libssl-dev
RUN luarocks-5.3 install luasec
RUN luarocks-5.3 install luaposix
RUN apt install -y git
RUN apt install -y libsqlite3-dev
RUN luarocks-5.3 install luasql-sqlite3
RUN luarocks-5.3 install luasocket
RUN luarocks-5.3 install crc32
WORKDIR /
COPY vts.luc .
COPY vts.db .
COPY key.pem .
COPY cert.pem .
CMD ["lua5.3", "./vts.luc", "-s"]
