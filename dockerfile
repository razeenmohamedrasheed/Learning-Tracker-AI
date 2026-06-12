# -------------------------------------------------------
# Base image
# python:3.11-slim-bookworm — Debian 12 base
# fewer CVEs than plain slim (older Debian 11)
# -------------------------------------------------------
FROM python:3.11-slim-bookworm

# set working directory inside container
WORKDIR /app

# -------------------------------------------------------
# Install system deps needed by asyncpg + psycopg2
# -------------------------------------------------------
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------------
# Install Python dependencies
# Copy requirements first — Docker caches this layer
# Only re-runs if requirements.txt changes
# -------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------------
# Copy app code
# -------------------------------------------------------
COPY . .

# expose port FastAPI runs on
EXPOSE 8000

# -------------------------------------------------------
# Start command
# --host 0.0.0.0 → accept connections from outside container
# --port 8000
# -------------------------------------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]