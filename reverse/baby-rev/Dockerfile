FROM ubuntu:22.04 AS builder

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY src/challenge.c .
RUN gcc -O2 -o challenge challenge.c && strip --strip-all challenge

# ─────────────────────────────────────────────────────────────────────────────

FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y xinetd && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash ctf

RUN mkdir -p /challenge
COPY --from=builder /build/challenge /challenge/challenge
RUN chown root:ctf /challenge/challenge && chmod 750 /challenge/challenge

COPY xinetd.conf        /etc/xinetd.conf
COPY xinetd.d/baby-rev  /etc/xinetd.d/baby-rev
COPY run.sh             /challenge/run.sh
COPY start.sh           /start.sh
RUN chmod 755 /challenge/run.sh /start.sh

EXPOSE 9999
CMD ["/start.sh"]
