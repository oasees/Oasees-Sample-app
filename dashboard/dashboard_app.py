from flask import Flask, render_template, jsonify
import requests
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Parse sensor endpoints from environment
SENSORS = os.environ.get('SENSORS', '').split(',')
sensor_endpoints = []
for sensor in SENSORS:
    if sensor.strip():
        host, port = sensor.strip().split(':')
        sensor_endpoints.append(f"http://{host}:{port}")

# Store latest sensor data
sensor_cache = {}

def fetch_sensor_data():
    """Background thread to fetch data from all sensors"""
    while True:
        for endpoint in sensor_endpoints:
            try:
                response = requests.get(f"{endpoint}/metrics", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    data["value"] = data[data['sensor_type']+"_value"]
                    data['timestamp'] = datetime.now().isoformat()
                    del data[data['sensor_type']+"_value"]
                    sensor_cache[endpoint] = {
                        **data,
                        'last_updated': datetime.now().isoformat(),
                        'status': 'online'
                    }
                else:
                    sensor_cache[endpoint] = {
                        'sensor_name': f'Sensor at {endpoint}',
                        'status': 'error',
                        'last_updated': datetime.now().isoformat()
                    }
            except Exception as e:
                sensor_cache[endpoint] = {
                    'sensor_name': f'Sensor at {endpoint}',
                    'status': 'offline',
                    'error': str(e),
                    'last_updated': datetime.now().isoformat()
                }
        time.sleep(3)  # Fetch every 3 seconds

# Start background thread
if sensor_endpoints:
    fetch_thread = threading.Thread(target=fetch_sensor_data, daemon=True)
    fetch_thread.start()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/sensors')
def api_sensors():
    """API endpoint to get all sensor data"""
    return jsonify(sensor_cache)

@app.route('/api/sensor/<path:endpoint>')
def api_sensor(endpoint):
    """Get data for a specific sensor"""
    full_endpoint = f"http://{endpoint}"
    return jsonify(sensor_cache.get(full_endpoint, {}))

if __name__ == '__main__':
    print(f"Starting Dashboard with sensors: {sensor_endpoints}")
    app.run(host='0.0.0.0', port=5000, debug=False)