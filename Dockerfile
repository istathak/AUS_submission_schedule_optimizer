# Use Python 3.11 slim image (lightweight)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy data file
COPY data/Schedule_Historical_Data.csv data/

# Copy application code
COPY api/ api/
COPY src/ src/

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port 5001
EXPOSE 5001

# Set working directory for imports
ENV PYTHONPATH=/app

# Run the Flask application
CMD ["python", "api/app.py"]
