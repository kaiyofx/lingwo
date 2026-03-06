FROM python:3.13.2-slim
WORKDIR /qdrant_updater

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 6333
CMD [ "python", "./qdrant_init.py" ]
