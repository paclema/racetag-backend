FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

# Set workdir to project root inside image
WORKDIR /app

# Install runtime dependencies first for better layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire app (excluding items in .dockerignore)
COPY . /app

# Expose default uvicorn port
EXPOSE 8000

# Move to the python package folder
WORKDIR /app/racetag-backend

# Start FastAPI app (module path is racetag-backend/app.py)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]