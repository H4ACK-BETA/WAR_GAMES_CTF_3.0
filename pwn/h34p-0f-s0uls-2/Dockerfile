FROM ubuntu:20.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY src/challenge.c .
RUN gcc -o challenge challenge.c \
    -pie -fPIE \
    -fno-stack-protector \
    -Wl,-z,relro,-z,lazy \
    -O0 -g0 && \
    strip --strip-all challenge

# --- Runtime (glibc 2.31 — Ubuntu 20.04) ---

FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y xinetd && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash ctf

RUN mkdir -p /challenge
COPY --from=builder /build/challenge /challenge/challenge
RUN chown root:ctf /challenge/challenge && chmod 750 /challenge/challenge

COPY xinetd.conf                  /etc/xinetd.conf
COPY xinetd.d/h34p-0f-s0uls-2    /etc/xinetd.d/h34p-0f-s0uls-2
COPY run.sh                       /challenge/run.sh
COPY start.sh                     /start.sh
RUN chmod 755 /challenge/run.sh /start.sh

EXPOSE 9999
CMD ["/start.sh"]
