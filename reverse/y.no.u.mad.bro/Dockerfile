FROM debian:bookworm-slim AS builder
RUN apt-get update && \
    apt-get install -y gcc libc6-dev python3 && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY src/challenge.c src/gen_challenge.py ./
RUN mkdir -p /tmp/build && \
    python3 gen_challenge.py "matrix-root-v1" && \
    gcc -fno-stack-protector -no-pie -z execstack -O0 \
        -o /build/challenge /tmp/build/challenge.c && \
    cp /build/challenge /build/challenge_dist && \
    strip --strip-all /build/challenge_dist

FROM scratch AS dist
COPY --from=builder /build/challenge_dist /challenge

FROM debian:bookworm-slim AS runtime
RUN apt-get update && \
    apt-get install -y xinetd && \
    rm -rf /var/lib/apt/lists/*
RUN useradd -m -s /usr/sbin/nologin ctf
RUN mkdir -p /challenge
COPY --from=builder /build/challenge /challenge/challenge
RUN chown root:ctf /challenge/challenge && chmod 750 /challenge/challenge
COPY xinetd.conf            /etc/xinetd.conf
COPY xinetd.d/matrix-root-access /etc/xinetd.d/matrix-root-access
COPY run.sh                 /challenge/run.sh
COPY start.sh               /start.sh
RUN chmod 755 /challenge/run.sh /start.sh
EXPOSE 9888
CMD ["/start.sh"]
