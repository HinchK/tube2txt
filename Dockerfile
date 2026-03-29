# Stage 1: Build Gridland TUI
FROM oven/bun:1 AS tui-builder
WORKDIR /tui
COPY tui/package.json tui/bun.lock ./
RUN bun install --frozen-lockfile
COPY tui/ .
RUN bun run build-web

# Stage 2: Python runtime
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Copy source and config
COPY src/ ./src/
COPY pyproject.toml .
COPY README.md .
COPY styles.css ./src/tube2txt/styles.css

# Install Python dependencies
# We rely on the pip package for yt-dlp to ensure it's in the correct environment
RUN pip install --no-cache-dir .

# Copy built TUI assets
COPY --from=tui-builder /tui/dist ./static/
# Create projects directory
RUN mkdir -p /app/projects

EXPOSE 8000

# Use the installed entry point for reliability
CMD ["tube2txt-hub"]
