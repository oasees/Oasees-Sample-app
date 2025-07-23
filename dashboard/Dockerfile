FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files first
COPY dashboard_app.py .

# Create templates directory and copy template
COPY templates/ templates/

# Debug: List files to verify structure
RUN ls -la && ls -la templates/

# Expose port
EXPOSE 5000

# Run the dashboard application
CMD ["python", "dashboard_app.py"]