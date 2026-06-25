FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

RUN dpkg --add-architecture i386 && \
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc g++ make pkg-config nasm \
        gcc-multilib g++-multilib \
        autoconf automake libtool gettext \
        wget curl ca-certificates bzip2 \
        libc6-dev-i386 lib32z1-dev \
        libc6:i386 libstdc++6:i386 \
        ffmpeg \
        python3 python3-pip python3-setuptools python3-dev \
        gdb \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN wget -q https://download.videolan.org/pub/vlc/0.9.4/vlc-0.9.4.tar.bz2 \
    && tar xf vlc-0.9.4.tar.bz2 \
    && rm vlc-0.9.4.tar.bz2

WORKDIR /build/vlc-0.9.4

COPY src/fix_configure.py /tmp/fix_configure.py
RUN python3 /tmp/fix_configure.py configure

RUN for f in $(find modules/ src/ -name '*.c'); do \
      grep -q '_GNU_SOURCE' "$f" || sed -i '1i #define _GNU_SOURCE' "$f"; \
    done

RUN ln -sf /bin/bash /bin/sh
SHELL ["/bin/bash", "-c"]
RUN CFLAGS="-m32 -g -O0 -fno-stack-protector -fno-pie -U_FORTIFY_SOURCE -Wno-error -w -std=gnu99" \
    CXXFLAGS="-m32 -g -O0 -fno-stack-protector -fno-pie -U_FORTIFY_SOURCE -Wno-error -w" \
    LDFLAGS="-m32 -z execstack -z norelro -no-pie -lpthread" \
    CONFIG_SHELL=/bin/bash \
    /bin/bash ./configure \
      --prefix=/opt/vlc \
      --host=i686-linux-gnu \
      --build=i686-linux-gnu \
      --disable-nls \
      --disable-rpath \
      --disable-taglib \
      --disable-id3tag \
      --disable-schroedinger \
      --disable-ncurses \
      --disable-atmo \
      --disable-remoteosd \
      --disable-audioscrobbler \
      --disable-mmx \
      --disable-sse \
      --disable-optimizations \
      --disable-sout \
      --disable-httpd \
      --disable-vlm \
      --disable-mad \
      --disable-avcodec \
      --disable-avformat \
      --disable-swscale \
      --disable-postproc \
      --disable-a52 \
      --disable-libmpeg2 \
      --disable-vorbis \
      --disable-ogg \
      --disable-speex \
      --disable-flac \
      --disable-x264 \
      --disable-png \
      --disable-alsa \
      --disable-pulse \
      --disable-xcb \
      --disable-xvideo \
      --disable-glx \
      --disable-freetype \
      --disable-fribidi \
      --disable-fontconfig \
      --disable-qt4 \
      --disable-skins2 \
      --disable-dbus \
      --disable-dbus-control \
      --disable-hal \
      --disable-gnutls \
      --disable-libgcrypt \
      --disable-libxml2 \
      --enable-run-as-root \
    2>&1 | tee /build/configure.log ; \
    test -f Makefile || (echo "=== CONFIGURE FAILED ===" && tail -80 /build/configure.log && false)

RUN make -k -j"$(nproc)" 2>&1 | tee /build/make.log ; \
    echo "Make exit code: $?"

RUN make install 2>&1 || true

RUN find modules/ -path '*/.libs/lib*_plugin.so' | while read so; do \
      subdir=$(echo "$so" | sed 's|^modules/||; s|/\.libs/.*||'); \
      mkdir -p "/opt/vlc/lib/vlc/${subdir}"; \
      cp -v "$so" "/opt/vlc/lib/vlc/${subdir}/"; \
    done

RUN echo "/opt/vlc/lib" > /etc/ld.so.conf.d/vlc.conf && ldconfig

RUN file /opt/vlc/bin/vlc && /opt/vlc/bin/vlc --version 2>&1 | head -3
RUN file /opt/vlc/lib/vlc/demux/libsubtitle_plugin.so

RUN ffmpeg -y -f lavfi -i color=c=black:s=320x240:d=5 \
        -c:v libx264 -pix_fmt yuv420p \
        /opt/dummy.mp4

RUN rm -rf /build

WORKDIR /app
RUN pip3 install flask==2.0.3 werkzeug==2.0.3 jinja2==3.0.3 markupsafe==2.0.1

COPY src/app.py          /app/app.py
COPY src/templates/       /app/templates/
COPY src/entrypoint.sh    /entrypoint.sh
RUN  chmod +x /entrypoint.sh

COPY flag.txt /flag.txt
RUN chmod 444 /flag.txt

RUN useradd -m -s /bin/bash relay \
    && chown relay:relay /flag.txt

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]
