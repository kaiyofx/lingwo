FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем в /app/api, чтобы импорт api.main работал при PYTHONPATH=/app
COPY . /app/api

ENV PYTHONPATH=/app
EXPOSE 8001

CMD ["uvicorn", "api.main:APP", "--host", "0.0.0.0", "--port", "8001"]
