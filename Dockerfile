FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Create working directory
WORKDIR /app

# Install dependencies
COPY pyproject.toml .
# We use pip to install the current directory which reads pyproject.toml
RUN pip install --no-cache-dir .

# Copy application code
COPY src/ src/
COPY data/ data/
COPY credentials/ credentials/

# Expose port
EXPOSE 8080

# Command to run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
