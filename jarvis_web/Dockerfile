# LEO OS — Cloud Always-On Container
FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    openssl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarını kopyala
COPY . .

# Ortam değişkenleri
ENV PORT=8765
ENV PYTHONUNBUFFERED=1
ENV JARVIS_PUBLIC=0

EXPOSE 8765

CMD ["python", "server.py", "--host", "0.0.0.0", "--no-ssl"]
