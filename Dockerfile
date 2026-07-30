FROM python:3.10-slim

WORKDIR /app

# Install ffmpeg for Whisper audio transcription and system tools
RUN apt-get update && apt-get install -y ffmpeg curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source code and configuration
COPY src/ ./src/
COPY configs/ ./configs/
COPY scripts/ ./scripts/
COPY .env* env* ./

EXPOSE 8000

# Run the application using the new src.main entry point
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
