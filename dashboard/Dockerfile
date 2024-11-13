FROM python:3.10-slim-bookworm AS base
WORKDIR /app/dashboard

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

ENV API_URL=http://localhost:5001

EXPOSE 8501

# Add requirements.txt
ADD requirements.txt /app/dashboard/requirements.txt

# Install dependencies
RUN pip install -r requirements.txt

# Add source code
ADD . /app/dashboard/

# Set up healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Copy entrypoint
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]