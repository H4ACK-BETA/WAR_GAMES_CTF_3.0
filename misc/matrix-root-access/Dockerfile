# matrix://root_access -- GZCTF challenge image
#
# Stage 1 (builder): generate a per-image random secret phrase + XOR key,
#   patch chall.c, compile with intentionally weakened protections.
# Stage 2 (runtime): slim image, non-root user, xinetd front-end, flag
#   injected at container start from GZCTF_FLAG (never baked into the image).

# ---------- Stage 1: builder ----------
FROM debian:bookworm-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libc6-dev \
        python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY chall.c gen_challenge.py ./

# Each `docker build` invocation (one per team, per GZCTF's dynamic
# container provisioning) gets its own random secret phrase + XOR key
# unless a fixed seed is passed via --build-arg for reproducible testing.
ARG BUILD_SEED=""
RUN mkdir -p /tmp/build \
    && python3 gen_challenge.py "${BUILD_SEED}" \
    && gcc -fno-stack-protector -no-pie -z execstack -O0 \
           -o /build/chall /tmp/build/chall.c

# ---------- Stage 2: runtime ----------
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        xinetd \
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

# start.sh runs as root (needed to write/chown the flag file before
# xinetd drops to the unprivileged `ctf` user per connection, per the
# user= directive in /etc/xinetd.d/ctf).
ENTRYPOINT ["/start.sh"]
