# Use an official Python base image
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

# Copy requirements first (better for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install "fastapi[standard]"
# Copy the rest of the code
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the app
CMD ["fastapi", "run", "main.py"]