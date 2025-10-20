# Use official Python slim image
FROM python:3.11-slim

# Avoid buffering, show logs immediately
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Install apt dependencies required for building some wheels (kept minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose port used by aiohttp health endpoint
EXPOSE 8080

# Default command - runs bot.py which creates aiohttp listener on $PORT
CMD ["python", "bot.py"]
