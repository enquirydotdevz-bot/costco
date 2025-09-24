# ============================
# Step 1: Base image
# ============================
FROM python:3.11-slim

# ============================
# Step 2: Set working directory
# ============================
WORKDIR /app

# ============================
# Step 3: Copy files
# ============================
COPY . /app

# ============================
# Step 4: Install system dependencies
# ============================
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ============================
# Step 5: Install Python dependencies
# ============================
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# ============================
# Step 6: Expose port
# ============================
EXPOSE 8000

# ============================
# Step 7: Set environment variables (optional)
# ============================
# You can override these in Render environment
ENV DB_NAME=costco_db
ENV DB_USER=postgres
ENV DB_PASSWORD=yourpassword
ENV DB_HOST=localhost
ENV DB_PORT=5432

# ============================
# Step 8: Start FastAPI server
# ============================
CMD ["uvicorn", "api_copy:app", "--host", "0.0.0.0", "--port", "8000"]
