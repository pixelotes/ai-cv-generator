# --- Stage 1: Base Image & System Dependencies ---
# Use an official Python runtime as a parent image. slim-buster is a good balance of size and functionality.
FROM python:3.11-slim-buster

# Set the maintainer label
LABEL maintainer="Your Name <you@example.com>"

# --- Environment Variables ---
# Set environment variables to make the container configurable
# Note: For connecting to services on the host from a Docker container,
# 'host.docker.internal' is a special DNS name that resolves to the host's internal IP.
# This assumes your scraper and Ollama are running on your local machine, accessible from Docker.
ENV PYTHONUNBUFFERED=1 \
    FLASK_HOST=0.0.0.0 \
    FLASK_PORT=5001 \
    SCRAPER_API_URL=http://host.docker.internal:3000/scrape \
    OLLAMA_API_URL=http://host.docker.internal:11434

# --- System Dependencies ---
# Install system packages required for WeasyPrint (a PDF generation library).
# We also install build-essential for any packages that might need compilation.
# Using --no-install-recommends keeps the image size smaller.
# We clean up the apt cache in the same RUN command to reduce image layer size.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# --- Application Setup ---
# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker's layer caching.
# This layer will only be rebuilt if the requirements.txt file changes.
COPY requirements.txt .

# Install Python dependencies from the requirements file.
# --no-cache-dir reduces the image size by not storing the pip cache.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application source code into the container.
# This includes app.py and the 'templates' directory.
COPY . .

# --- Running the Application ---
# Expose the port the app runs on. This should match the FLASK_PORT env var.
EXPOSE 5001

# Define the command to run the application using Gunicorn, a production-ready WSGI server.
# This is more robust than running with Flask's built-in development server.
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--timeout", "120", "app:app"]
