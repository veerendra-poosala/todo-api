# ---- Base image: small official Python image ----
FROM python:3.13-slim

# Don't write .pyc files; flush logs straight to the console
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

# Install dependencies first so this layer is cached until requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Run as a non-root user
RUN useradd --create-home appuser && chown -R appuser /code
USER appuser

EXPOSE 8000

# Start the server (Beanie connects and creates indexes on startup; no migrations needed)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
