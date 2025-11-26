FROM python:3.12-slim

WORKDIR /app

# Install system dependencies commonly required for Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose the default port used by the app (can be overridden via PORT env)
EXPOSE 8000

# Default command: prefer running with uvicorn if available (common for FastAPI),
# otherwise fall back to running main.py or enhanced_api.py directly.
# This keeps the image flexible across different setups in the repo.
CMD ["python","main.py"]
