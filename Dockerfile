FROM python:3.10-slim

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

# Install Python dependencies with dependency cache optimization
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Runtime configuration
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
EXPOSE $PORT

# Optimized Gunicorn configuration
CMD exec gunicorn --bind :$PORT --workers 1 --threads 4 --timeout 120 app:server