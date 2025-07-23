FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the sensor application
COPY sensor_app.py .

# Expose port
EXPOSE 5000

# Run the sensor application
CMD ["python", "sensor_app.py"]