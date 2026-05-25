FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for psycopg2 and faster-whisper
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Pre-install CPU version of PyTorch to prevent downloading the massive 6GB CUDA version
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu --no-cache-dir

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

