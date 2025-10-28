# Use official Python image
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Copy files
COPY . .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
