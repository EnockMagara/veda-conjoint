# Veda Conjoint Experiment - Production Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Default port
ENV PORT=5000

# Expose port
EXPOSE 5000

# Run with gunicorn for production
ENTRYPOINT ["sh", "-c"]
CMD ["exec gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 120 run:app"]
