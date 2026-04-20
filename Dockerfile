# ---- frontend build stage ----
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- runtime stage ----
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    cp /root/.local/bin/uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY indie_market_analyst ./indie_market_analyst
COPY backtest ./backtest
COPY config ./config
RUN uv sync --frozen --no-dev

# Bundle frontend build
COPY --from=frontend /app/frontend/dist ./frontend/dist

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "indie_market_analyst.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
