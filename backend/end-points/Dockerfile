# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy project files and install Python dependencies
COPY pyproject.toml .
RUN uv sync --no-dev

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app \
    && cp /root/.local/bin/uv /usr/local/bin/uv \
    && chmod +x /usr/local/bin/uv
USER app

# Expose port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run the application with uvicorn
CMD ["uv", "run", "uvicorn", "agent_call:app", "--host", "0.0.0.0", "--port", "8080"]