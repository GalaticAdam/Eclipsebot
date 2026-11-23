FROM python:3.12-slim

WORKDIR /app

# System deps kept minimal; screenfetch/neofetch are optional in main.py
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Runtime state and secrets live on the host via the ./data volume mount
CMD ["python", "-u", "main.py"]
