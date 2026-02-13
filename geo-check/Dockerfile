FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends wget && rm -rf /var/lib/apt/lists/*
RUN wget -q -O /app/GeoLite2-Country.mmdb "https://github.com/rabuchaim/geolite2mirror/releases/download/20260210/GeoLite2-Country.mmdb"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
EXPOSE 8080
CMD ["uvicorn", "main:APP", "--host", "0.0.0.0", "--port", "8080"]
