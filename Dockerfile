FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    libspatialindex-dev \
    libgeos-dev \
    libproj-dev \
    libgdal-dev \
    python3-dev \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

ENV PORT=8080
ENV GUNICORN_CMD_ARGS="--workers=1 --threads=4 --timeout 120"
CMD ["gunicorn", "app:server"]