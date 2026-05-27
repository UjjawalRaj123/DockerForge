FROM python:3.11-slim-bullseye

# Clear corrupted cache, bypass clock drift, and disable HTTP pipelining (fixes Hash Sum mismatch)
RUN rm -rf /var/lib/apt/lists/* && apt-get clean && \
    apt-get -o Acquire::Check-Valid-Until=false \
            -o Acquire::Check-Date=false \
            -o Acquire::http::Pipeline-Depth=0 \
            -o Acquire::http::No-Cache=true \
            update && apt-get install -y --no-install-recommends \
    docker.io \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set the Python path so absolute imports like 'from app.agent...' work correctly
ENV PYTHONPATH="/"

EXPOSE 8501

# Health check for Streamlit
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app/main.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0"]