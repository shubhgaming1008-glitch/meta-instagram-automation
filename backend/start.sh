#!/bin/bash
# Start Celery worker in the background
celery -A app.core.celery_app worker --loglevel=info &

# Start FastAPI server in the foreground
# Render automatically injects the $PORT environment variable
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
