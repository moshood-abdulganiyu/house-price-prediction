FROM python:3.12-slim

# Copy official pre-compiled uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Ensure installed binaries in .venv are available on system PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy dependency files first
COPY pyproject.toml uv.lock ./

# Install production dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY . .

# Install project root if applicable
RUN uv sync --frozen --no-dev

EXPOSE 8000

# Render sets $PORT at runtime; default to 8000 locally
CMD ["sh", "-c", "uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8000}"]