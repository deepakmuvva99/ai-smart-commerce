FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY core_backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY core_backend /app/core_backend

# Expose port (Internal to Docker network)
EXPOSE 8000

# Start Gunicorn with Uvicorn workers for production scalability
CMD ["uvicorn", "core_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
