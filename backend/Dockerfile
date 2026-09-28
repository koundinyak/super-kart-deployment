# Small official Python image
FROM python:3.11-slim

# Working directory inside the container
WORKDIR /app

# Install dependencies first (Docker caches this layer -> faster rebuilds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the API code and the serialized model
COPY . .

# The API listens on 7860
EXPOSE 7860

# Start the production server: 2 workers, module 'app', Flask object 'superkart_api'
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:7860", "app:superkart_api"]
