FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy pyproject.toml and README.md for dependency installation
COPY pyproject.toml README.md ./

# Install Python dependencies from pyproject.toml
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run migrations and seed data, then start the application
CMD alembic upgrade head && \
    python scripts/seed_data.py && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000
