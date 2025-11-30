#!/bin/bash
set -euxo pipefail

cp /etc/vsftpd/vsftpd.conf.template /etc/vsftpd/vsftpd.conf # Copies the template configuration file. We use this because every time we start a container the script will run and, if we don't specify this, the properties will be added every time

# The tee command adds the properties and we also make sure to use the ENV variables defined in our Dockerfile

tee -a /etc/vsftpd/vsftpd.conf <<EOF

# Enables passive mode, useful when the server is behind a firewall or NAT
pasv_enable=YES
# Docker already runs the container in a secure sandbox. We set this to don't have any weird issues
seccomp_sandbox=NO
# Best practice for compatibility with modern users
utf8_filesystem=YES
# Used to manage passive communications
pasv_address=${PASV_ADDRESS}
pasv_min_port=${PASV_MIN_PORT}
pasv_max_port=${PASV_MAX_PORT}
EOF

cp /etc/vsftpd/vsftpd.conf /etc/vsftpd.conf

# Restarting and enabling vsftpd (may be redundant)
service vsftpd restart

python server.py
