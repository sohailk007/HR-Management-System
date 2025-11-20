# ====================== Stage 1: Builder ======================
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv & uvx from the official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy only requirements first (better layer caching)
COPY requirements.txt .

# Install dependencies into system Python (so they can be copied)
RUN uv pip install --system -r requirements.txt

# Copy the actual source code
COPY . .

# ====================== Stage 2: Final Runtime Image ======================

FROM python:3.12-slim



ENV PYTHONDONTWRITEBYTECODE=1 \

    PYTHONUNBUFFERED=1



WORKDIR /app



# Install postgresql-client

RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client && rm -rf /var/lib/apt/lists/*



# Copy uv & uvx (optional, but useful for runtime tools like "uv pip install" if needed)

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/



# Copy installed packages from builder (including all dependencies)

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

COPY --from=builder /usr/local/bin /usr/local/bin



# Install gunicorn (still as root - no permission issues)

RUN uv pip install --system gunicorn



# Copy application code

COPY --from=builder /app /app



# Create non-root user and fix permissions

RUN adduser --system --group --no-create-home appuser \

    && chown -R appuser:appuser /app



# Switch to non-root user (safe now)

USER appuser



EXPOSE 7000



CMD ["bash", "entrypoint.sh"]
