FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV PYTHONUTF8=1
ENV PORT=8080

# Create working directory
WORKDIR /app

# Install dependencies first (layer cached unless pyproject.toml changes)
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code only — NO credentials or .env files
# OAuth token is injected at runtime from Google Secret Manager (GOOGLE_OAUTH_TOKEN_JSON)
# Gemini API key is injected at runtime from Google Secret Manager (GEMINI_API_KEY)
COPY src/ src/

# Create empty data dir for SQLite (only used in local dev; prod uses Firestore)
RUN mkdir -p data

# Expose port
EXPOSE 8080

# Command to run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
