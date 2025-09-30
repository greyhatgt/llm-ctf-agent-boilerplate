FROM python:3.11-slim

WORKDIR /app

# Install Flask
RUN pip install Flask==2.3.3

# Copy application files
COPY app.py /app/

# Expose port 80
EXPOSE 80

# Set environment variable for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=80

# Run the application
CMD ["python", "-m", "flask", "run"]