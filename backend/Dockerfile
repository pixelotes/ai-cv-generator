# Stage 1: Use the official Playwright base image
# This image comes with Python 3.11 and all necessary system dependencies for Playwright browsers.
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker's layer caching.
# This step will only be re-run if requirements.txt changes.
COPY requirements.txt .

# Install the Python dependencies specified in requirements.txt
# --no-cache-dir reduces the image size.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY main.py .

# Create a non-root user for security purposes
# --disabled-password ensures no password is set
# --gecos '' provides empty GECOS field
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
# Switch to the non-root user
USER appuser

# Expose the port the application will run on
EXPOSE 8000

# Set a health check to verify the API is running
# This helps Docker manage the container's state, e.g., for restarts or in Swarm/Kubernetes.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# The command to run the application using Uvicorn ASGI server
# This is the entrypoint of the container.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
