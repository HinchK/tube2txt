# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install yt-dlp
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp && \
    chmod a+rx /usr/local/bin/yt-dlp

# Set working directory
WORKDIR /app

# Copy requirement files
COPY tube2txt.py .
COPY tube2txt.sh .
COPY hub.py .
COPY styles.css .

# Install Python dependencies
RUN pip install --no-cache-dir google-genai python-dotenv fastapi uvicorn

# Make scripts executable
RUN chmod +x tube2txt.sh

# Create output structure
RUN mkdir -p /app/projects

# Default port for the Hub
EXPOSE 8000

# Entrypoint allows running the Hub or the Processing script
# By default, start the Hub
CMD ["python3", "hub.py"]
