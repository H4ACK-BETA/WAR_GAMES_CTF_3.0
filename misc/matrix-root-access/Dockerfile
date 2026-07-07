FROM debian:bookworm-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libc6-dev python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY chall.c gen_challenge.py ./

ARG BUILD_SEED=""
RUN mkdir -p /tmp/build \
    && python3 gen_challenge.py "${BUILD_SEED}" \
    && gcc -fno-stack-protector -no-pie -z execstack -O0 \
           -o /build/chall /tmp/build/chall.c

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends xinetd \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /usr/sbin/nologin ctf

WORKDIR /home/ctf
COPY --from=builder /build/chall /home/ctf/chall
COPY ctf.xinetd /etc/xinetd.d/ctf
COPY start.sh /start.sh

RUN echo "Blocked by xinetd" > /etc/banner_fail \
    && chmod 555 /home/ctf/chall \
    && chmod 500 /start.sh \
    && chown root:root /start.sh /etc/xinetd.d/ctf /etc/banner_fail

EXPOSE 9999
ENTRYPOINT ["/start.sh"]
