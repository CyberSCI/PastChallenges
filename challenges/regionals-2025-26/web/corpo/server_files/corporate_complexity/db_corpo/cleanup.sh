#!/bin/sh

MYSQL_DATABASE="corpo"
MYSQL_USER="corpo"
MYSQL_PASSWORD="qkQv8bS6Qa5Yc1KVTV0bbi9a"

mysql -u corpo -p"$MYSQL_ROOT_PASSWORD" corpo -e "DELETE FROM tokens WHERE created_at < NOW() - INTERVAL 30 MINUTE;"

report_name=$(date +"orders_%Y%m%d%H%M%S.csv")
mysql -u corpo -p"$MYSQL_ROOT_PASSWORD" corpo -e "SELECT * FROM orders LIMIT 10 INTO OUTFILE '/db/$report_name' FIELDS TERMINATED BY ',' ENCLOSED BY '\"' LINES TERMINATED BY '\n';"

rm /db/cleanup.old.sh