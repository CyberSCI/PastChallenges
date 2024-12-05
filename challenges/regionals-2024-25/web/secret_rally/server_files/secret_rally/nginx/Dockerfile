FROM nginx

RUN rm /etc/nginx/conf.d/default.conf
COPY web.conf /etc/nginx/conf.d/

RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/nginx-selfsigned.key -out /etc/ssl/certs/nginx-selfsigned.crt -subj "/C=CA/O=Here Is/OU=The Flag/CN=Just Kidding"