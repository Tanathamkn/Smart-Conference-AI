FROM nvidia/cuda:12.2.2-runtime-ubuntu22.04

WORKDIR /app

# 2. Install Python 3.11 and necessary system tools
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-dev \
    build-essential \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 3. Set Python 3.11 as the system default (Fixed with -sf)
RUN ln -sf /usr/bin/python3.11 /usr/bin/python \
    && ln -sf /usr/bin/pip3 /usr/bin/pip

COPY requirements.txt .

# 4. Install the CUDA 12 optimized version of PyTorch
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cu121

# 5. Install the rest of your application dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]