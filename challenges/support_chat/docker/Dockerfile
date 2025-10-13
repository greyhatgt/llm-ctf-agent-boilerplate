# Prebuilt with Chromium + deps; avoids install failures
FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1

# App deps
RUN pip install --upgrade pip && pip install Flask==2.3.3 && pip install playwright

# Copy app
COPY app.py /app/app.py

# Expose HTTP
EXPOSE 80

# Environment (override via challenge.json)
ENV FLAG="flag{admin_cookie_xss_works}" \
    ADMIN_TOKEN="adm1n_tok3n_default" \
    SECRET_KEY="dev_secret_key_change_me" \
    HOST="0.0.0.0" \
    PORT="80"

CMD ["python", "/app/app.py"]