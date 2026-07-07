FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends zip && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir scapy flask gunicorn

WORKDIR /app
COPY src/ ./src/

COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8080
CMD ["/start.sh"]
