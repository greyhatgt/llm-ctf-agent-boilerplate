FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install flask

# Copy application files
COPY app.py /app/
COPY templates/ /app/templates/
COPY init_db.py /app/

# Initialize database
RUN python init_db.py

EXPOSE 80

CMD ["python", "app.py"]