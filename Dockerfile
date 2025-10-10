FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY analytics_requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r analytics_requirements.txt

# Copy application files
COPY analytics_server.py .
COPY analytics.py .

# Create directory for SQLite database
RUN mkdir -p /app/data

# Expose port
EXPOSE 5000

# No environment variables needed - server works out of the box

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/stats || exit 1

# Run the analytics server
CMD ["python", "analytics_server.py"]
