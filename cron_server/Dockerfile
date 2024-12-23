# Use the official Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8049

# Start the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8049"]