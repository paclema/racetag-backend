FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PORT=8000

# Set workdir to project root inside image
WORKDIR /app

# Install runtime dependencies first for better layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire app (excluding items in .dockerignore)
COPY . /app

# Expose default uvicorn port (container runtime port). You can override with -p during docker run.
EXPOSE 8000

# Move to the python package folder
WORKDIR /app/racetag-backend

# Start FastAPI app (module path is racetag-backend/app.py), honor PORT env variable
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]