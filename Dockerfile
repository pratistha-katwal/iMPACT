FROM python:3.10-slim  # Changed base image

# Install system dependencies with cleanup
RUN apt-get update && \
    apt-get install -y \
    libspatialindex-dev \
    libgeos-dev \
    libproj-dev \
    libgdal-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies in two stages for better caching
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Runtime configuration
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
EXPOSE $PORT

# Start command with optimized Gunicorn settings
CMD exec gunicorn --bind :$PORT --workers 1 --threads 4 --timeout 120 app:server