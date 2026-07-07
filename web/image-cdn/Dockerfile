FROM python:3.11-slim

# Install ImageMagick (with SVG support via librsvg)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        imagemagick \
        librsvg2-bin \
        libmagickwand-dev \
    && rm -rf /var/lib/apt/lists/*

# Install intentionally permissive ImageMagick policy
COPY policy.xml /etc/ImageMagick-6/policy.xml

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY metadata-service/ ./metadata-service/

# Create upload directories
RUN mkdir -p /app/uploads /app/processed

# Start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8080
CMD ["/start.sh"]
