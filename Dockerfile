# ============================
# Step 1: Base image
# ============================
FROM python:3.11-bullseye

# ============================
# Step 2: Set working directory
# ============================
WORKDIR /app

# ============================
# Step 3: Copy project files
# ============================
COPY . /app

# ============================
# Step 4: Install system dependencies + Chromium
# ============================
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    wget \
    curl \
    unzip \
    gnupg \
    xvfb \
    chromium \
    libnss3 \
    libgconf-2-4 \
    libxss1 \
    libappindicator3-1 \
    fonts-liberation \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ============================
# Step 5: Upgrade pip and install Python dependencies
# ============================
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# ============================
# Step 6: Environment variables
# ============================
ENV DB_NAME=costco_db
ENV DB_USER=postgres
ENV DB_PASSWORD=yourpassword
ENV DB_HOST=localhost
ENV DB_PORT=5432
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_PATH=/usr/bin/chromium
ENV PYTHONUNBUFFERED=1

# ============================
# Step 7: Expose port
# ============================
EXPOSE 8000

# ============================
# Step 8: Start FastAPI server
# ============================
CMD ["uvicorn", "api_copy:app", "--host", "0.0.0.0", "--port", "8000"]
