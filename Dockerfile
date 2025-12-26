# Use an official lightweight Python image as the base
FROM python:3.11-slim

# Make Python output unbuffered so logs appear immediately
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system-level dependencies (build tools, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copy the Python dependency list into the image
COPY requirements.txt .

# Install Python dependencies inside the container
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the image
COPY . .

# Copy the entrypoint script and make it executable
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Define the default process to run when the container starts
ENTRYPOINT ["docker-entrypoint.sh"]