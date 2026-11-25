# CyberSci Regionals 2026/27
#
# Log Monitor by Dmitriy Beryoza (0xd13a@gmail.com)

FROM ubuntu:24.04

ARG ELASTIC_VERSION=7.17.29
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/jdk/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl libatomic1 openjdk-11-jre-headless \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system elk \
    && useradd --system --gid elk --home-dir /opt/elk --shell /usr/sbin/nologin elk \
    && mkdir -p /opt/jdk /opt/elk/elasticsearch /opt/elk/logstash /opt/elk/kibana /var/lib/elasticsearch \
    && cd /tmp \
    && for component in elasticsearch logstash kibana; do \
         case "$component" in \
           logstash) archive="logstash-${ELASTIC_VERSION}-linux-x86_64.tar.gz" ;; \
           *) archive="${component}-${ELASTIC_VERSION}-linux-x86_64.tar.gz" ;; \
         esac; \
         curl -fLsS --retry 3 -o "$archive" "https://artifacts.elastic.co/downloads/$component/$archive" \
         && curl -fLsS --retry 3 -o "$archive.sha512" "https://artifacts.elastic.co/downloads/$component/$archive.sha512" \
         && sha512sum -c "$archive.sha512" \
         && tar -xzf "$archive" -C "/opt/elk/$component" --strip-components=1 \
         && rm -f "$archive" "$archive.sha512" || exit 1; \
       done \
    && chown -R elk:elk /opt/elk /var/lib/elasticsearch

COPY canvas-workpad.json /tmp
COPY --chmod=755 start.sh /usr/local/bin/start-elk
USER elk
WORKDIR /opt/elk
EXPOSE 9200 5601 5000 5001 5002
ENTRYPOINT ["/usr/local/bin/start-elk"]
