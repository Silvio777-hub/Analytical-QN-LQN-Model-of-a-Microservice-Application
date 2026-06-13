# Dockerfile for SPE Performance Modeling & Analysis
# Enables running all analysis scripts in an isolated container environment

FROM python:3.11-slim

WORKDIR /app

# Copy dependency requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the scripts, data, and configuration files
COPY . .

# Environment configuration
ENV PYTHONUNBUFFERED=1

# Default command prints help usage
CMD ["python", "scripts/model/queueing_network.py", "--help"]
