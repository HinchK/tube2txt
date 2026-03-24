# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install yt-dlp
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp && \
    chmod a+rx /usr/local/bin/yt-dlp

# Set working directory
WORKDIR /app

# Copy requirement files first for better caching
COPY tube2txt.py .
COPY tube2txt.sh .
COPY styles.css .

# Install Python dependencies
RUN pip install --no-cache-dir google-genai python-dotenv

# Make scripts executable
RUN chmod +x tube2txt.sh

# Create output directory
RUN mkdir /output
WORKDIR /output

# Set entrypoint to the shell script
ENTRYPOINT ["/app/tube2txt.sh"]
