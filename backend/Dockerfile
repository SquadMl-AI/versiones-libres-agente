# Use the official Python image as the base
# This uses Python 3.11 with the "slim" variant to keep the image lightweight

FROM python:3.11-slim

# Set the working directory inside the container
# All subsequent commands will be executed in this directory
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y locales && \
    sed -i '/es_ES.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen es_ES.UTF-8 && \
    rm -rf /var/lib/apt/lists/*
ENV LANG=es_ES.UTF-8
ENV LANGUAGE=es_ES:es
ENV LC_ALL=es_ES.UTF-8

# Copy the requirements.txt file first to leverage Docker's caching mechanism
# This ensures that dependencies are only reinstalled if requirements.txt changes
COPY requirements.txt .

# Install the necessary packages specified in requirements.txt
# The --no-cache-dir option prevents temporary files from being cached, keeping the image smaller
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
# This includes all files in the current directory (context) into /app in the container
COPY . .

# Expose port 8000 to allow external access to the application
# This is for documentation purposes and doesn't automatically open the port
EXPOSE 5555

# Command to run the FastAPI application using Uvicorn ASGI server
# - "api.app:app" specifies the module (api.app) and application instance (app)
# - "--host 0.0.0.0" makes the app accessible from outside the container
# - "--port 8000" sets the port where Uvicorn will listen for incoming requests
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5555"]