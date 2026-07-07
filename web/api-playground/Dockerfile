FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/

# Generate proto stubs at build time
COPY gen_proto.sh .
RUN bash gen_proto.sh

EXPOSE 8080 50051

# Start script handles flag + launches the app
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
