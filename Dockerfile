# Multi-stage Dockerfile for Pokemon Scouting app

# ===== Builder stage: install dependencies into a virtualenv =====
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv

RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /build

# Install system deps only if needed (kept minimal for this project)
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# ===== Runtime stage: copy app and run =====
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    FLASK_ENV=production \
    SQLALCHEMY_DATABASE_URI=sqlite:///instance/pokemon.db

# Create a non-root user
RUN useradd -m appuser

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY app ./app
COPY requirements.txt README.md pyproject.toml ./
COPY app/db/pokemon_list.csv ./app/db/pokemon_list.csv

# Ensure a writable directory for SQLite and fix ownership
RUN mkdir -p /app/instance && chown -R appuser:appuser /app

EXPOSE 5000

USER appuser

CMD ["python", "-m", "app.main"]