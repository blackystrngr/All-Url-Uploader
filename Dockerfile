FROM python:3.10-slim

# Install system dependencies
RUN apt-get update -y && apt-get upgrade -y && \
    apt-get install -y ffmpeg curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create downloads directory with proper permissions
RUN mkdir -p DOWNLOADS && chmod 755 DOWNLOADS

# Set environment variables
ENV PYTHONUNBUFFERED=1

EXPOSE $PORT

CMD ["python", "app.py"]
