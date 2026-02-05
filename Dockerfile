# Multi-stage build for React + FastAPI application served by nginx
FROM node:18-alpine as frontend-build

# Set working directory
WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install frontend dependencies
RUN npm ci --only=production=false

# Copy frontend source code
COPY frontend/ .

# Build the frontend application
RUN npm run build

# Python backend setup
FROM python:3.11-slim as backend-setup

# Set working directory
WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ .

# Production stage with nginx
FROM nginx:alpine

# Install Python and supervisor
RUN apk add --no-cache python3 py3-pip supervisor

# Create application directory
WORKDIR /app

# Copy Python dependencies from backend-setup stage
COPY --from=backend-setup /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-setup /usr/local/bin /usr/local/bin

# Copy built frontend from frontend-build stage
COPY --from=frontend-build /app/frontend/build /usr/share/nginx/html

# Copy backend application
COPY --from=backend-setup /app/backend /app/backend

# Copy supervisord configuration
COPY supervisord.conf /etc/supervisord.conf

# Create nginx configuration
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    \
    # Frontend - serve static files \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
    \
    # Backend API - proxy to FastAPI \
    location /api/ { \
        proxy_pass http://127.0.0.1:8085/; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
        proxy_redirect off; \
    } \
    \
    error_page 500 502 503 504 /50x.html; \
    location = /50x.html { \
        root /usr/share/nginx/html; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Set environment variables for backend
ENV HOST=127.0.0.1
ENV PORT=8085
ENV PYTHONPATH=/app/backend

# Expose port 80
EXPOSE 80

# Start both nginx and FastAPI using supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]