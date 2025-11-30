FROM ubuntu:25.04

ARG VNC_PW="changeme"
ENV DEBIAN_FRONTEND=noninteractive \
    VNC_PW=${VNC_PW} \
    USER="dockeruser"

RUN apt-get update && apt-get install -y \
    x11-apps \
    tigervnc-standalone-server \
    wine \
    unzip \
    sudo \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash ${USER} && \
    echo "${USER} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER ${USER}
WORKDIR /home/${USER}

COPY dist.zip /home/${USER}/dist.zip
RUN unzip dist.zip
RUN ls
RUN cd dist/

# --- VNC xstartup Script ---
# Create the xstartup script to launch xclock.
RUN mkdir -p /home/${USER}/.config/tigervnc && \
    echo "${VNC_PW}" | vncpasswd -f > /home/${USER}/.config/tigervnc/passwd && \
    chmod 600 /home/${USER}/.config/tigervnc/passwd && \
    echo "#!/bin/bash" > /home/${USER}/.config/tigervnc/xstartup && \
    echo "cd ~/dist/" > /home/${USER}/.config/tigervnc/xstartup && \
    echo "exec wine IdleFroggoFishing.exe" >> /home/${USER}/.config/tigervnc/xstartup && \
    chmod +x /home/${USER}/.config/tigervnc/xstartup

EXPOSE 5901
CMD ["/usr/bin/vncserver", ":1", "-geometry", "800x600", "-fg", "-localhost", "no"]
