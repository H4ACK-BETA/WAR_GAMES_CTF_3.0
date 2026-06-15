FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim

COPY --from=builder /install /usr/local

WORKDIR /app

COPY chall.py /app/chall.py
COPY start.sh /app/start.sh

RUN chmod 755 /app/start.sh \
    && chmod 644 /app/chall.py

ENV FLAG=""

USER root

EXPOSE 1338

CMD ["/app/start.sh"]
