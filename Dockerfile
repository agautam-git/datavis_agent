# ── Base image ────────────────────────────────────────────────────
FROM python:3.11-slim

# ── Set working directory ─────────────────────────────────────────
WORKDIR /app

# ── Install system dependencies ───────────────────────────────────
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Copy dependency files first (layer caching) ───────────────────
COPY pyproject.toml .

# ── Install Python dependencies ───────────────────────────────────
RUN pip install --no-cache-dir -e .

# ── Copy source code ──────────────────────────────────────────────
COPY src/ ./src/

# ── Set Python path ───────────────────────────────────────────────
ENV PYTHONPATH=/app/src

# ── Expose port ───────────────────────────────────────────────────
EXPOSE 8000

# ── Run the API ───────────────────────────────────────────────────
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]