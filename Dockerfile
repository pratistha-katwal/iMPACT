# Use official Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose the port the app runs on
EXPOSE $PORT

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app_dash:app.server"]