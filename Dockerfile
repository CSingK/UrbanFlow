# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Expose the Cloud Run port
EXPOSE 8080

# Environment variables
ENV PORT=8080
ENV API_BASE_URL=http://localhost:8000/api/v1

# Start both FastAPI and Streamlit
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 & streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0"]
