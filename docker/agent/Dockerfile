FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    net-tools \
    netcat-traditional \
    nmap \
    sqlmap \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -e .

# Copy the agent code
COPY agent/ /app/agent/
COPY helper/ /app/helper/
COPY docker/agent/run_agent.py /app/

CMD ["python", "run_agent.py"]