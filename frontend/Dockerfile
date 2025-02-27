FROM python:3.13.2-slim
LABEL author="kaiyo"

WORKDIR /app
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

COPY . .
RUN pip install -r requirements.txt
EXPOSE 80
EXPOSE 443
HEALTHCHECK CMD curl --fail http://localhost/_stcore/health
ENTRYPOINT [ "streamlit", "run", "main.py", "--server.port=80", "--server.address=0.0.0.0" ]