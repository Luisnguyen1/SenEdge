# Use a Python 3.11 base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create cache directory with proper permissions
RUN mkdir -p /cache && chmod 777 /cache

# Set the cache directory to a writable location in Hugging Face Spaces
ENV TRANSFORMERS_CACHE="/cache"
ENV HF_HOME="/cache"
ENV HF_DATASETS_CACHE="/cache"

# Copy the rest of the application
COPY . .

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=7860
ENV DEBUG=False

# Expose the port that Hugging Face Spaces expects
EXPOSE 7860

# Command to run the application
CMD ["python", "app.py"]