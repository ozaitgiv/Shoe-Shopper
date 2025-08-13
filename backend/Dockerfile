FROM python:3.11-slim

# Install all system dependencies in a single layer with proper cleanup
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code
COPY . .

# Create startup script with full paths and use PORT environment variable
RUN echo '#!/bin/sh\n/usr/local/bin/python manage.py migrate\n/usr/local/bin/python manage.py collectstatic --noinput\n/usr/local/bin/gunicorn shoe_shopper.wsgi:application --bind 0.0.0.0:${PORT:-10000}' > /app/start.sh
RUN chmod +x /app/start.sh

# Default command
CMD ["/app/start.sh"]