FROM python:3.12-slim

# Copy official pre-compiled uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy dependency definition files
COPY pyproject.toml uv.lock ./

# Sync production dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy project files
COPY . .

# Final sync to include project root
RUN uv sync --frozen --no-dev

EXPOSE 8000

# Use full path to uvicorn inside virtual environment
CMD ["sh", "-c", "/app/.venv/bin/uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8000}"]