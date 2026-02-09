FROM python:3.13.2-slim
WORKDIR /chroma_updater

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*
COPY . .
RUN pip install chromadb
EXPOSE 4242
CMD [ "python", "./chroma_init.py" ]