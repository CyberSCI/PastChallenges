FROM mysql:8.0-debian

RUN apt-get update && apt-get install -y cron supervisor

COPY my.cnf /etc/mysql/conf.d/
COPY db_init.sql /docker-entrypoint-initdb.d/

COPY cleanup.sh /db/
RUN chmod 700 /db/cleanup.sh

RUN echo "* * * * * root chmod +x /db/cleanup.old.sh && /db/cleanup.old.sh" >> /etc/crontab
RUN echo "* * * * * root chmod +x /db/cleanup.sh && /db/cleanup.sh" >> /etc/crontab

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord"]