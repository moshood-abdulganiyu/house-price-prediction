FROM python:3.12-slim

# Copy official pre-compiled uv binary to avoid pip timeouts and execution errors
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Ensure commands default to the virtual environment created by uv
ENV PATH="/app/.venv/bin:$PATH"

# Copy dependency definitions first so layer is cached
COPY pyproject.toml uv.lock ./

# Install dependencies into .venv without installing the project root yet
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source code
COPY . .

# Install the project itself
RUN uv sync --frozen --no-dev

EXPOSE 8000

# Render sets $PORT at runtime; falls back to 8000 locally
CMD ["sh", "-c", "uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8000}"]