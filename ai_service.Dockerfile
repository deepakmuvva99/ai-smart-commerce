FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (required for LightGBM/PyTorch)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY ai_service/requirements.txt /app/requirements.txt
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

# Copy application source
COPY ai_service /app/ai_service

# Expose port
EXPOSE 8001

# Start FastAPI application
CMD ["uvicorn", "ai_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
