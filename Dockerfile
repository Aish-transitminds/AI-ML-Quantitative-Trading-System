# Stage 1: Build the React Frontend
FROM node:20 AS frontend-builder
WORKDIR /app/web
COPY web/package*.json ./
RUN npm install
COPY web/ ./
RUN npm run build

# Stage 2: Build the Python Backend
FROM python:3.10-slim
WORKDIR /app

# Install system dependencies required for scientific Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend dependencies and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source files
COPY . .

# Copy built frontend assets from Stage 1
COPY --from=frontend-builder /app/web/dist ./web/dist

# Expose port (Cloud providers dynamically assign this via the PORT environment variable)
ENV PORT=8000
EXPOSE $PORT

# Start the unified FastAPI backend (serving API and static React files)
CMD ["sh", "-c", "python run.py --host 0.0.0.0 --port ${PORT} --no-browser"]
