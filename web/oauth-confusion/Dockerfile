FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/

EXPOSE 8080 9000

# Start script handles flag + launches both servers
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
