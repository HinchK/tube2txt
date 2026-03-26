# Stage 1: Build Gridland TUI
FROM oven/bun:1 AS tui-builder
WORKDIR /tui
COPY tui/package.json tui/bun.lock ./
RUN bun install --frozen-lockfile
COPY tui/ .
RUN bun run build

# Stage 2: Python runtime
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp && \
    chmod a+rx /usr/local/bin/yt-dlp

WORKDIR /app

COPY src/ ./src/
COPY pyproject.toml .
COPY README.md .
COPY styles.css .

RUN pip install --no-cache-dir .

# Copy built TUI assets
COPY --from=tui-builder /tui/dist ./tui-dist/

RUN mkdir -p /app/projects

# Bake in stable defaults so Railway works without manual env-var config.
# TUBE2TXT_DB must live inside the mounted volume (/app/projects) so the
# database survives container restarts.
# TUBE2TXT_TUI_DIR points to where the multi-stage build places the TUI
# bundle; the pip-installed hub.py cannot resolve this via __file__ because
# site-packages is several directories removed from /app.
ENV TUBE2TXT_DB=/app/projects/tube2txt.db \
    TUBE2TXT_TUI_DIR=/app/tui-dist

EXPOSE 8000

CMD ["tube2txt-hub"]
