# LEO OS — Cloud 24/7 Always-On Container (Render / Railway / Koyeb)
FROM python:3.11-slim

WORKDIR /app

# Sistem paketleri
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    openssl \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Bağımlılıklar
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt || true
COPY jarvis_web/requirements.txt ./requirements_web.txt
RUN pip install --no-cache-dir -r requirements_web.txt

# Proje dosyalarını kopyala
COPY . .

# Ortam değişkenleri
ENV PORT=8765
ENV PYTHONUNBUFFERED=1
ENV JARVIS_PUBLIC=0

EXPOSE 8765

CMD ["python", "jarvis_web/server.py", "--host", "0.0.0.0", "--no-ssl"]
