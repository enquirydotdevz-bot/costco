FROM python:3.11-slim

WORKDIR /app
COPY . /app

# Install dependencies + Chromium + ChromeDriver
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    wget \
    unzip \
    gnupg \
    xvfb \
    chromium \
    chromium-driver \
    libnss3 \
    libgconf-2-4 \
    libxss1 \
    libappindicator3-1 \
    fonts-liberation \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python packages
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Environment variables
ENV DB_NAME=costco_db
ENV DB_USER=postgres
ENV DB_PASSWORD=yourpassword
ENV DB_HOST=localhost
ENV DB_PORT=5432
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_PATH=/usr/bin/chromium

EXPOSE 8000

CMD ["uvicorn", "api_copy:app", "--host", "0.0.0.0", "--port", "8000"]
